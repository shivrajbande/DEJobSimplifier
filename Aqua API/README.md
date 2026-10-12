# Multimodal Text-to-SQL & Data Intelligence Multi-Agent System

An enterprise-grade, multimodal AI analytics platform and text-to-SQL orchestration system. The system translates natural language queries and document/image inputs (such as dashboards, database schemas, reports, and charts) into verified, executable MySQL queries, safely executes them against a relational database, and delivers synthesized business insights.

---

## 1. Core Purpose & Capabilities

- **Multimodal Ingestion**: Ingests both plain text user queries and visual assets (images, screenshots, invoices, dashboard mockups, data schemas).
- **Intelligent Triage & Intent Classification**: Deconstructs user queries and document context into structured analytical targets, generating a noise-free `refined_execution_plan`.
- **Semantic Schema Retrieval (RAG)**: Uses dense vector embeddings in ChromaDB to retrieve only the relevant table DDLs and column relationships required for the query.
- **Constrained SQL Generation**: Synthesizes high-performance MySQL queries (SELECT queries, VIEWS, and materialized tables) adhering strictly to retrieved schema boundaries.
- **Programmatic Validation & Self-Healing**: Validates SQL using AST/keyword security guardrails and MySQL `EXPLAIN` dry-runs; autonomously feeds runtime errors back to the generator for self-healing (up to 4 attempts).
- **Safe Query Execution**: Executes validated SQL queries in isolated database transactions, returning top result records.
- **Human-in-the-Loop (HITL) Interruption**: Pauses graph execution when requirements are ambiguous or critical information is missing, capturing user clarification via LangGraph interrupts before resuming.
- **Insight Synthesis**: Translates raw database rows into direct, natural-language business answers and architectural explanations.
- **Real-Time Streaming**: Streams stage-by-stage node status updates and final insights via FastAPI Server-Sent Events (SSE).

---

## 2. System Architecture & Workflow

The orchestration engine is built as a stateful directed graph using **LangGraph** with a **SQLite checkpointer** (`state_db.sqlite`) for session persistence.

```
                    User Query / Image Upload
                               │
                               ▼
                     [SUPERVISOUR_NODE]
                               │
            ┌──────────────────┴──────────────────┐
     (Has Image)                           (Text Only)
            ▼                                     ▼
 [DOCUMENT_ANALYZER_NODE]              [INTENT_CLASSIFIER_NODE]
            │                                     ▲
            │ (Extracted Context)                 │
            └─────────────────────────────────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │ (Ambiguity Detected)      │ (Clear Intent)
                 ▼                           ▼
            [HITL_NODE]             Semantic Schema Lookup (ChromaDB)
          (Interrupt/Pause)                  │
                                             ▼
                                   [SQL_GENERATOR_NODE] ◄──────────────┐
                                             │                         │
                                             ▼                         │ (Self-Healing
                                   [SQL_VALIDATOR_NODE]                │  on Error,
                                             │                         │  Max 4 Retries)
                                             ├─── [Invalid Syntax/DB Err] ─┘
                                             │
                                             ├─── [Exceeded Retries] ──> [HITL_NODE]
                                             │
                                             ▼ [Valid Query & Executed Data]
                                  [INSIGHTS_GENERATOR_NODE]
                                             │
                                             ▼
                                           (END)
```

---

## 3. Node Responsibilities

| Node Name | Model / Engine | Core Responsibility |
| :--- | :--- | :--- |
| **`SUPERVISOUR_NODE`** | Rule-based triage | Evaluates input payload; routes multimodal requests to `DOCUMENT_ANALYZER_NODE` and pure text queries to `INTENT_CLASSIFIER_NODE`. |
| **`DOCUMENT_ANALYZER_NODE`** | `llama-4-scout-17b-16e-instruct` (Groq Vision) | Analyzes uploaded images/documents; extracts structured sections, tables, metrics, entities, and detects visual ambiguities. |
| **`INTENT_CLASSIFIER_NODE`** | `llama-3.1-8b-instant` (Groq) | Analyzes user objectives; produces a `refined_execution_plan`; invokes `semantic_search_tool` to fetch matching DDL schemas from vector memory. |
| **`SQL_GENERATOR_NODE`** | `llama-3.3-70b-versatile` (Groq) | Translates the execution plan and retrieved schema into MySQL syntax with strict formatting, table aliasing, and backtick delimiters. |
| **`SQL_VALIDATOR_NODE`** | Programmatic MySQL Engine | Applies security filters (blocks `DROP`, `TRUNCATE`, `DELETE`); validates query via `EXPLAIN`; executes query to fetch up to 10 result rows; triggers self-healing on failure. |
| **`INSIGHTS_GENERATOR_NODE`** | `llama-3.3-70b-versatile` (Groq) | Interprets query execution results to answer the user's analytical goal directly, or provides a step-by-step structural explanation if requested. |
| **`HITL_NODE`** | LangGraph `interrupt()` | Pauses execution state for human input/clarification (single-select, multi-select, or text) and updates conversation memory upon resume. |

---

## 4. State Schema (`AgentState`)

The shared hierarchical graph state comprises five sub-states:

- **`messages`**: Chronological message history with LangChain `add_messages` reducer.
- **`raw_user_query`** / **`uploaded_image`**: Original user prompt and base64-encoded image data URI.
- **`DocumentState`**: Stores `document_type`, `extracted_sections`, `detected_entities`, `detected_usecases`, `overall_summary`, `total_no_of_sections`, and `relevant_schema`.
- **`ClarificationState`**: Tracks `clarification_needed`, `clarification_attempt`, `clarification_history`, and `section_clarifications`.
- **`WorkflowState`**: Controls flow navigation with `workflow_stage`, `next_step`, `return_to`, `status`, and `primary_intent`.
- **`ExecutionState`**: Holds `refined_execution_plan`, `reasoning_summary`, `generated_sql`, `sql_error`, `query_results` (actual DB rows), and `generated_insights`.
- **`pending_clarification`**: Staging payload for HITL prompts.

---

## 5. Semantic Schema Retrieval (RAG)

- **Vector Database**: ChromaDB (`./embedding_memory`) with collection name `sql_schema`.
- **Embedding Model**: HuggingFace `sentence-transformers/all-MiniLM-L6-v2`.
- **Indexed Schema Scope**: 12 detailed relational schemas covering the IMDB domain (`movies`, `persons`, `cast_details`, `directors`, `reviews`, `awards`, `box_office`, `genre_stats`, `streaming`, `production`, `users`, `soundtracks`), embedded with column definitions, primary/foreign key relationships, analytical usage, and typical query patterns.

---

## 6. Technology Stack

- **Framework & Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph), [LangChain](https://github.com/langchain-ai/langchain)
- **API Server**: [FastAPI](https://fastapi.tiangolo.com/) with Server-Sent Events (SSE) streaming
- **LLM Providers**: Groq API (`llama-3.1-8b-instant`, `llama-3.3-70b-versatile`, `llama-4-scout`)
- **Vector Search**: ChromaDB, HuggingFace Embeddings (`all-MiniLM-L6-v2`)
- **Relational Database**: MySQL (`mysql-connector-python`)
- **Persistence & Checkpointing**: SQLite (`state_db.sqlite` with `SqliteSaver`)
- **Package & Runtime Manager**: `uv` / Python 3.13+

---

## 7. API Reference & Execution

### Endpoint: `POST /query/{targetId}`
Streams execution milestones and the final analytical answer using Server-Sent Events (`text/event-stream`).

#### Request Payload
```json
{
  "query": "Which actors earned the highest salary in Action movies released after 2020?",
  "image": "data:image/jpeg;base64,...", // Optional base64-encoded image
  "session_id": "session-uuid-1234"      // Optional thread ID for persistent state
}
```

#### Event Stream Output
```
data: {"type": "status", "node": "SUPERVISOUR_NODE", "message": "📋 Triaging user query..."}
data: {"type": "status", "node": "INTENT_CLASSIFIER_NODE", "message": "🔍 Classifying intent and loading database schemas..."}
data: {"type": "status", "node": "SQL_GENERATOR_NODE", "message": "✍️ Generating SQL query..."}
data: {"type": "status", "node": "SQL_VALIDATOR_NODE", "message": "🛡️ SQL validation successful"}
data: {"type": "status", "node": "INSIGHTS_GENERATOR_NODE", "message": "✨ Compiling final insights..."}
data: {"type": "final", "content": "The top-earning actor in Action movies released after 2020 is ..."}
data: [DONE]
```

### Running the Application
```bash
# Start the FastAPI dev server
uv run fastapi dev main.py
```
