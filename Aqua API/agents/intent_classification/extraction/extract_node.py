
import json
import functools
from agents.intent_classification.extraction.extract_prompt import EXTRACT_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import AgentState
from typing import Literal
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


# Keep text as a span of the question, never a rewritten phrase.

# 2. Don’t show it the schema
# It’s tempting to include column names so the model can “pick the right one”. Don’t. That is linking’s job, and a model given column names will invent matches that look confident and wrong. Extraction should work identically on any database, which also makes it reusable across your vertical domains.

# 3. Use an LLM with structured output
# Rules and spaCy are a trap for this step. “Premium customer revenue by month for 2025” has overlapping noun phrases that rules split badly. Use your small model (the 8B on Groq is enough) with:
# JSON-schema-constrained output (or JSON mode plus pydantic validation)
# temperature 0
# 6 to 10 few-shot examples covering the awkward cases (see section 7), taken from BIRD training questions


# 4. Validate in code after the call
# Substring check. Every text and filter value must appear in the question, case-insensitively. Drop or retry any that don’t, since that is how you catch hallucinations.
# Regex union for literals. Also collect quoted strings, numbers and capitalized tokens by regex, and add any the model missed. Cheap insurance for the values the keyword index depends on.
# Dates resolved by code. The LLM only extracts “last quarter”, and a date library turns it into a range. You must pass “today” into that function. Never ask the model to compute dates.
# Normalize. Lowercase, trim and de-duplicate, and fold overlapping spans (“revenue” inside “premium customer revenue”).


# 5. Handle implicit things
# “How many customers...” has no metric word, but implies COUNT of customers. Set aggregation_hint="count" and emit “customers” as the thing counted.
# “Top 5 products by sales” gives an order/limit of 5, a group-by of “products” and a metric of “sales”.
# Comparisons (“more than 100”) need the operator and value split correctly.


# 6. Evaluating extraction
# Hand-labeling mentions doesn’t scale, so derive weak labels from the gold SQL with sqlglot:
# every literal in a WHERE clause should appear among your extracted filter values (literal recall, the most useful check)
# aggregate functions suggest metrics, and GROUP BY columns suggest dimensions
# Don’t chase extraction accuracy for its own sake. The metric that decides whether it works is whether column recall@k rises downstream compared with the whole-question control (keep that control query running).

# 7. Cases to test deliberately
# compound phrases (“premium customer revenue”), where metric and filter blend
# the same word meaning a filter in one question and a column in another
# negation (“excluding refunds”, “not in California”)
# multiple values (“California and Texas”)
# questions with no explicit metric
# follow-up questions that depend on the previous turn (“what about last year?”), which need conversation state resolved before extraction

# Once it’s stable, the output feeds straight into the linker: metrics, group-bys and time go to the schema index, and filters with values go to the keyword index.
class Mention(BaseModel):
    text: str                 # exact span copied from the question
    

class Filter(Mention):
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "between", "in", "like"] = "="
    value: str | list[str] | None = None   # "Nike", "5", ["CA","NY"]
    column_hint: str | None = None         # the words describing the column, e.g. "brand"
    negated: bool = False 

class Extraction(BaseModel):
    select: list[Mention] = Field(default_factory=list) 
    metrics: list[Mention]=Field(default_factory=list)    # "revenue", "number of orders"
    group_by: list[Mention]=Field(default_factory=list)   # "by month", "per region"
    filters: list[Filter]=Field(default_factory=list)     # "for Nike", "orders over 100"
    time: list[Mention]=Field(default_factory=list)       # "in 2025", "last quarter"
    order_limit: list[Mention]=Field(default_factory=list)  # "top 5", "highest"
    aggregation_hint: str | None=Field(default=None)  # "sum", "avg", "count" if stated or implied ("how many")


import re

def clean_numeric_value(val: str | None) -> str | None:
    """Strips currency symbols and commas from currency/formatted numbers without breaking IDs or hyphenated strings."""
    if not isinstance(val, str):
        return val
    cleaned = val.strip()
    # Strip currency symbols and commas if it's formatted like $1,900 or 1,000,000 or $500
    if re.fullmatch(r"[-+]?[\$€£₹]?\s*[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?\s*%?", cleaned) or re.fullmatch(r"[-+]?[\$€£₹]\s*[0-9]+(?:\.[0-9]+)?", cleaned):
        return re.sub(r"[\$€£₹,]", "", cleaned).strip()
    return cleaned

def normalize_extraction(ex: Extraction) -> Extraction:
    """Normalizes extracted values after passing the grounding check."""
    for f in ex.filters:
        if isinstance(f.value, list):
            f.value = [clean_numeric_value(v) for v in f.value]
        elif isinstance(f.value, str):
            f.value = clean_numeric_value(f.value)
    return ex

def keep_grounded(ex:Extraction,query:str)->Extraction:
    q = query.lower()
    ok = lambda s:s is not None and s.lower() in q

    for name in ("select", "metrics", "group_by", "time", "order_limit"):
        if hasattr(ex, name):
            setattr(ex, name, [m for m in getattr(ex, name) if ok(m.text)])
    ex.filters = [
        f for f in ex.filters
        if ok(f.text) and all(ok(v) for v in (f.value if isinstance(f.value, list) else [f.value]))
    ]
    return ex
    

def make_extraction_node(llm):
    def extraction_node(state: AgentState):
        query = state["raw_user_query"].strip()
        messages = [
            SystemMessage(content=EXTRACT_PROMPT + "\n\nRespond ONLY with a single valid raw JSON object matching the Extraction schema."),
            HumanMessage(content=query)
        ]
        error = None
        try:
            resp = llm.invoke(messages)
            text = resp.content.strip()
            if "```" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
            match = re.search(r"\{[\s\S]*\}", text)
            raw_dict = json.loads(match.group(0)) if match else json.loads(text)
            ex = Extraction.model_validate(raw_dict)
            grounded = keep_grounded(ex, query)
            result = normalize_extraction(grounded)
        except Exception as e:
            result = Extraction()
            error = str(e)
        
        return {
            "extraction": result.model_dump(),
            "extraction_error": error
        }
    
    return extraction_node

      
       

        