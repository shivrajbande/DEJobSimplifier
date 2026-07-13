from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from agents.orchestrator import orchestrator_agent
from typing import Optional
import json
from pydantic import BaseModel



app = FastAPI()

import uuid

class QueryRequest(BaseModel):
    query: str
    image: Optional[str] = None
    session_id: Optional[str] = None

    


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/query/{targetId}")
async def response_generator(targetId: str, request: QueryRequest):

    user_query = request.query
    image_url = request.image
    session_id = request.session_id or targetId or str(uuid.uuid4())

    session_config={"configurable":{"thread_id":session_id}}
    

    async def event_stream():
        try:
            inputs = {
                "messages": [HumanMessage(content=user_query)],
                "raw_user_query": user_query,
                "uploaded_image": image_url,
            }

            for event in orchestrator_agent.stream(inputs,config=session_config,stream_mode="updates"):
                print(f"DEBUG: Current Node -> {list(event.keys())}")
                for node_name, state_update in event.items():

                    # -------------------------
                    # 🧠 STATUS STREAMING
                    # -------------------------
                    if node_name == "SUPERVISOUR_NODE":
                        yield f"data: {json.dumps({
                            'type': 'status',
                            'node': node_name,
                            'message': '📋 Triaging user query...'
                        })}\n\n"

                    elif node_name == "DOCUMENT_ANALYZER_NODE":
                        yield f"data: {json.dumps({
                            'type': 'status',
                            'node': node_name,
                            'message': '📄 Analyzing uploaded document/image...'
                        })}\n\n"

                    elif node_name == "INTENT_CLASSIFIER_NODE":
                        yield f"data: {json.dumps({
                            'type': 'status',
                            'node': node_name,
                            'message': '🔍 Classifying intent and loading database schemas...'
                        })}\n\n"

                    elif node_name == "SQL_GENERATOR_NODE":
                        yield f"data: {json.dumps({
                            'type': 'status',
                            'node': node_name,
                            'message': '✍️ Generating SQL query...'
                        })}\n\n"

                    elif node_name == "SQL_VALIDATOR_NODE":
                        exec_state = state_update.get("execution", {})
                        sql_error = exec_state.get("sql_error") if isinstance(exec_state, dict) else None
                        if sql_error:
                            yield f"data: {json.dumps({
                                'type': 'status',
                                'node': node_name,
                                'message': f'❌ SQL validation failed: {sql_error}'
                            })}\n\n"
                        else:
                            yield f"data: {json.dumps({
                                'type': 'status',
                                'node': node_name,
                                'message': '🛡️ SQL validation successful'
                            })}\n\n"

                    elif node_name == "HITL_NODE":
                        yield f"data: {json.dumps({
                            'type': 'status',
                            'node': node_name,
                            'message': '⚠️ Awaiting human clarification or approval...'
                        })}\n\n"

                    elif node_name == "__interrupt__":
                        interrupt_info = state_update[0] if isinstance(state_update, (list, tuple)) else state_update
                        value = getattr(interrupt_info, "value", interrupt_info)
                        yield f"data: {json.dumps({
                            'type': 'interrupt',
                            'node': node_name,
                            'message': '⚠️ Action required: Clarification or input needed.',
                            'details': value
                        })}\n\n"
 
                    # -------------------------
                    # ✨ FINAL OUTPUT STREAM
                    # -------------------------
                    elif node_name == "INSIGHTS_GENERATOR_NODE":
                        yield f"data: {json.dumps({
                            'type': 'status',
                            'node': node_name,
                            'message': '✨ Compiling final insights...'
                        })}\n\n"

                        exec_state = state_update.get("execution", {})
                        raw_insights = exec_state.get("generated_insights") if isinstance(exec_state, dict) else None
                        if not raw_insights:
                            raw_insights = state_update.get("final_insights")

                        if isinstance(raw_insights, list) and len(raw_insights) > 0:
                            content = raw_insights[0].get("text", "")
                        else:
                            content = raw_insights or ""

                        if content:
                            yield f"data: {json.dumps({
                                'type': 'final',
                                'content': content
                            })}\n\n"

            # ✅ Done
            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({
                'type': 'error',
                'message': str(e)
            })}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
