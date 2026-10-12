import time
import json, random, hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from agents.intent_classification.extraction.extract_prompt import EXTRACT_PROMPT
from agents.intent_classification.extraction.extract_node import make_extraction_node

# from agents.orchestrator import orchestrator_agent
from typing import Optional
from pydantic import BaseModel
from collections import defaultdict




# app = FastAPI()

# import uuid

# class QueryRequest(BaseModel):
#     query: str
#     image: Optional[str] = None
#     session_id: Optional[str] = None

    


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# same question different db and also different column name
# TUNE_DBS = {"financial", "california_schools", "thrombosis_prediction", "codebase_community"}
# data = json.load(open("dev_databases/dev.json", "r"))
# tune    = [q for q in data if q["db_id"] in TUNE_DBS]       # you iterate on these
# heldout = [q for q in data if q["db_id"] not in TUNE_DBS]   # untouched until the end
# random.seed(42)
# by_db = defaultdict(list)
# for q in tune:
#     by_db[q["db_id"]].append(q)

# sample = []
# for qs in by_db.values():
#     random.shuffle(qs)
#     sample += qs[:15]

# for name, rows in [("tune", tune), ("heldout", heldout), ("extractor_sample", sample)]:
#     json.dump(rows, open(f"{name}.json", "w"), indent=2)


llm = init_chat_model('openai/gpt-oss-20b', model_provider='groq', temperature=0.1)
extractor_node = make_extraction_node(llm=llm)
prompt_hash = hashlib.md5(EXTRACT_PROMPT.encode()).hexdigest()[:8]
run_time = datetime.now().strftime("%Y%m%d_%H%M%S")
questions = json.load(open("extractor_sample.json"))
out_path = Path(f"extractor_sample_v{prompt_hash}_{run_time}.jsonl")
final_out_path = Path(f"extracted_sample_v{prompt_hash}_{run_time}.json")

done = set()

if out_path.exists():
    for line in out_path.open():
        line = line.strip()
        if line:
            row = json.loads(line)
            if row.get("error") is None:
                done.add(row["question_id"])

print(f"📊 Prompt version: v{prompt_hash}")
print(f"📁 Total questions: {len(questions)} | Already processed: {len(done)} | Remaining: {len(questions) - len(done)}")

with out_path.open("a") as f:
    for i, q in enumerate(questions, 1):
        if q["question_id"] in done:
            continue
        
        t0 = time.time()
        print(f"[{i}/{len(questions)}] Extracting QID {q['question_id']} ({q['db_id']})...", end=" ", flush=True)
        result = extractor_node({"raw_user_query": q["question"]})
        row = {
            "question_id": q["question_id"],
            "db_id": q["db_id"],
            "question": q["question"],
            "gold_sql": q["SQL"],
            "extraction": result.get("extraction"),
            "error": result.get("extraction_error"),
            "seconds": round(time.time() - t0, 2),
        }
        f.write(json.dumps(row) + "\n")
        f.flush()
        print(f"Done in {row['seconds']}s")
        time.sleep(0.3)


latest = {}

if out_path.exists():
    for line in out_path.open():
        line = line.strip()
        if line:
            row = json.loads(line)
            # Prefer successful extractions over failed rows
            if row["question_id"] not in latest or (row.get("error") is None and latest[row["question_id"]].get("error") is not None):
                latest[row["question_id"]] = row

json.dump(list(latest.values()), open(final_out_path, "w"), indent=2)
print(f"✅ Finished! Saved {len(latest)} records to {final_out_path}")

        


# @app.post("/query/{targetId}")
# async def response_generator(targetId: str, request: QueryRequest):

#     user_query = request.query
#     image_url = request.image
#     session_id = request.session_id or targetId or str(uuid.uuid4())

#     session_config={"configurable":{"thread_id":session_id}}
    

#     async def event_stream():
#         try:
#             inputs = {
#                 "messages": [HumanMessage(content=user_query)],
#                 "raw_user_query": user_query,
#                 "uploaded_image": image_url,
#             }

#             for event in orchestrator_agent.stream(inputs,config=session_config,stream_mode="updates"):
#                 print(f"DEBUG: Current Node -> {list(event.keys())}")
#                 for node_name, state_update in event.items():

#                     # -------------------------
#                     # 🧠 STATUS STREAMING
#                     # -------------------------
#                     if node_name == "SUPERVISOUR_NODE":
#                         yield f"data: {json.dumps({
#                             'type': 'status',
#                             'node': node_name,
#                             'message': '📋 Triaging user query...'
#                         })}\n\n"

#                     elif node_name == "DOCUMENT_ANALYZER_NODE":
#                         yield f"data: {json.dumps({
#                             'type': 'status',
#                             'node': node_name,
#                             'message': '📄 Analyzing uploaded document/image...'
#                         })}\n\n"

#                     elif node_name == "INTENT_CLASSIFIER_NODE":
#                         yield f"data: {json.dumps({
#                             'type': 'status',
#                             'node': node_name,
#                             'message': '🔍 Classifying intent and loading database schemas...'
#                         })}\n\n"

#                     elif node_name == "SQL_GENERATOR_NODE":
#                         yield f"data: {json.dumps({
#                             'type': 'status',
#                             'node': node_name,
#                             'message': '✍️ Generating SQL query...'
#                         })}\n\n"

#                     elif node_name == "SQL_VALIDATOR_NODE":
#                         exec_state = state_update.get("execution", {})
#                         sql_error = exec_state.get("sql_error") if isinstance(exec_state, dict) else None
#                         if sql_error:
#                             yield f"data: {json.dumps({
#                                 'type': 'status',
#                                 'node': node_name,
#                                 'message': f'❌ SQL validation failed: {sql_error}'
#                             })}\n\n"
#                         else:
#                             yield f"data: {json.dumps({
#                                 'type': 'status',
#                                 'node': node_name,
#                                 'message': '🛡️ SQL validation successful'
#                             })}\n\n"

#                     elif node_name == "HITL_NODE":
#                         yield f"data: {json.dumps({
#                             'type': 'status',
#                             'node': node_name,
#                             'message': '⚠️ Awaiting human clarification or approval...'
#                         })}\n\n"

#                     elif node_name == "__interrupt__":
#                         interrupt_info = state_update[0] if isinstance(state_update, (list, tuple)) else state_update
#                         value = getattr(interrupt_info, "value", interrupt_info)
#                         yield f"data: {json.dumps({
#                             'type': 'interrupt',
#                             'node': node_name,
#                             'message': '⚠️ Action required: Clarification or input needed.',
#                             'details': value
#                         })}\n\n"
 
#                     # -------------------------
#                     # ✨ FINAL OUTPUT STREAM
#                     # -------------------------
#                     elif node_name == "INSIGHTS_GENERATOR_NODE":
#                         yield f"data: {json.dumps({
#                             'type': 'status',
#                             'node': node_name,
#                             'message': '✨ Compiling final insights...'
#                         })}\n\n"

#                         exec_state = state_update.get("execution", {})
#                         raw_insights = exec_state.get("generated_insights") if isinstance(exec_state, dict) else None
#                         if not raw_insights:
#                             raw_insights = state_update.get("final_insights")

#                         if isinstance(raw_insights, list) and len(raw_insights) > 0:
#                             content = raw_insights[0].get("text", "")
#                         else:
#                             content = raw_insights or ""

#                         if content:
#                             yield f"data: {json.dumps({
#                                 'type': 'final',
#                                 'content': content
#                             })}\n\n"

#             # ✅ Done
#             yield "data: [DONE]\n\n"

#         except Exception as e:
#             yield f"data: {json.dumps({
#                 'type': 'error',
#                 'message': str(e)
#             })}\n\n"
#             yield "data: [DONE]\n\n"

#     return StreamingResponse(
#         event_stream(),
#         media_type="text/event-stream"
#     )


