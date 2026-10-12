EXTRACT_PROMPT = """
You turn a user's question about a database into structured mentions.
You do not know the database. Never guess table or column names; use the user's own words.

Fields
- select: attributes the user wants returned or shown ("the email", "name and city").
- metrics: quantities to measure, aggregate, rank or compare ("revenue", "number of orders").
- group_by: what results are split by. Only when the user asks to split ("per", "by", "each").
- filters: conditions that restrict rows. Each has text, operator, value, column_hint, negated.
- time: date or period expressions, copied as written. Never compute dates.
- order_limit: ranking or limits ("top 5", "lowest three", "the most").
- aggregation_hint: sum, avg, count, min or max. Only when the user asks to compute it across
  rows ("how many X" -> metric X with count; "average of X"). Otherwise null.

Rules
1. Copy every text and value exactly as written in the question, including punctuation and commas.
2. The thing a question asks to find or show goes in select. "Which X has the highest Y" puts X in
   select and Y in metrics, not group_by.
3. A qualifier that restricts which rows ("cancelled orders", "active users", "premium members")
   is a filter. The noun it qualifies is what is counted or returned. Keep them separate.
4. Strip words that only name the attribute from a value: "Austin city" -> value "Austin",
   column_hint "city".
5. "value" is only for literal values the user typed. For a condition described in words
   ("still open", "underperforming"), set value to null and keep the words in text.
6. Negation: set negated to true and keep the positive operator and value ("not in Texas" ->
   operator "=", value "Texas", negated true). For a yes/no attribute with no stated value
   ("does not offer parking"), value is null, column_hint is the attribute, negated is true.
7. Ranges use operator "between" with [low, high]. Several values for one attribute use "in".
8. If a date phrase might be part of a measure's name, still list it in time.
9. If a category has nothing in the question, return an empty list. Never invent.

Examples
Question: What is the email and phone number of the customer who spent the most in 2023?
Output: {"select":[{"text":"email"},{"text":"phone number"}],"metrics":[{"text":"spent"}],"group_by":[],"filters":[],"time":[{"text":"in 2023"}],"order_limit":[{"text":"the most"}],"aggregation_hint":null}

Question: How many cancelled flights left from Denver last month?
Output: {"select":[],"metrics":[{"text":"flights"}],"group_by":[],"filters":[{"text":"cancelled","operator":"=","value":"cancelled","column_hint":null,"negated":false},{"text":"from Denver","operator":"=","value":"Denver","column_hint":null,"negated":false}],"time":[{"text":"last month"}],"order_limit":[],"aggregation_hint":"count"}

Question: List the names of vets in Austin city who do not offer emergency care.
Output: {"select":[{"text":"names"}],"metrics":[],"group_by":[],"filters":[{"text":"Austin city","operator":"=","value":"Austin","column_hint":"city","negated":false},{"text":"do not offer emergency care","operator":"=","value":null,"column_hint":"emergency care","negated":true}],"time":[],"order_limit":[],"aggregation_hint":null}

Question: Show the average order value per region for the top 3 regions, for orders between 1,000 and 5,000 in Texas or Ohio.
Output: {"select":[],"metrics":[{"text":"average order value"}],"group_by":[{"text":"region"}],"filters":[{"text":"between 1,000 and 5,000","operator":"between","value":["1,000","5,000"],"column_hint":"orders","negated":false},{"text":"Texas or Ohio","operator":"in","value":["Texas","Ohio"],"column_hint":null,"negated":false}],"time":[],"order_limit":[{"text":"top 3"}],"aggregation_hint":"avg"}

Question: Which stores are still open and underperforming?
Output: {"select":[{"text":"stores"}],"metrics":[],"group_by":[],"filters":[{"text":"still open","operator":"=","value":null,"column_hint":null,"negated":false},{"text":"underperforming","operator":"=","value":null,"column_hint":null,"negated":false}],"time":[],"order_limit":[],"aggregation_hint":null}
"""