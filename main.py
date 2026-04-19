from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from agents.orchestrator import orchestrator_agent
import json
from pydantic import BaseModel



app = FastAPI()

class QueryRequest(BaseModel):
    query: str


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ for dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/query/{targetId}")
async def response_generator(targetId: str, request: QueryRequest):

    user_query = request.query

    async def event_stream():
        try:
            inputs = {"messages": [HumanMessage(content=user_query)]}

            for event in orchestrator_agent.stream(inputs, stream_mode="updates"):
                print(f"DEBUG: Current Node -> {list(event.keys())}")
                for node_name, state_update in event.items():

                    if "messages" not in state_update:
                        continue

                    last_msg = state_update["messages"][-1]

                    # -------------------------
                    # 🧠 STATUS STREAMING
                    # -------------------------
                    if node_name == "retriever_node":
                        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                            yield f"data: {json.dumps({
                                'type': 'status',
                                'node': node_name,
                                'message': '🔍 Searching knowledge base...'
                            })}\n\n"
                        else:
                            yield f"data: {json.dumps({
                                'type': 'status',
                                'node': node_name,
                                'message': '📋 Plan generated'
                            })}\n\n"

                    elif node_name == "tools":
                        yield f"data: {json.dumps({
                            'type': 'status',
                            'node': node_name,
                            'message': '🛠️ Executing tools...'
                        })}\n\n"

                    elif node_name == "sql_generator_node":
                        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                            yield f"data: {json.dumps({
                                'type': 'status',
                                'node': node_name,
                                'message': 'Generating SQL...'
                            })}\n\n"
                        else:
                            raw_insights = state_update.get("final_insights")

                            if len(raw_insights) > 0:
                                if(isinstance(raw_insights, list)):
                                    content = raw_insights[0].get("text", "")
                                    yield f"data: {json.dumps({
                                        'type': 'status',
                                        'node': node_name,
                                        'message': 'SQL error is {content}'
                                    })}\n\n"

                                else:
                                    content = raw_insights or ""
                                    yield f"data: {json.dumps({
                                        'type': 'status',
                                        'node': node_name,
                                        'message': 'SQL error is {content}'
                                    })}\n\n"

                          
                            else:
                                yield f"data: {json.dumps({
                                    'type': 'status',
                                    'node': node_name,
                                    'message': '✅ SQL ready'
                                })}\n\n"

                    # -------------------------
                    # ✨ FINAL OUTPUT STREAM
                    # -------------------------
                    elif node_name == "insights_generator_node":

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
