from typing import Optional, TypedDict, List, Dict, Any, Annotated, Union
from langgraph.graph import add_messages

class ClarificationState(TypedDict, total=False):
    clarification_needed: bool
    clarification_attempt: int
    clarification_history: List[Dict[str, str]]
    section_clarifications: List[Dict[str, Any]]  # Clean section-only schema tracking

class DocumentState(TypedDict, total=False):
    document_type: Optional[str]
    relevant_schema: Optional[str]        # Populated programmatically via DDL Embeddings
    extracted_sections: List[Dict[str, Any]]
    detected_entities: List[str]
    detected_usecases: List[str]
    overall_summary:str
    total_no_of_sections :int

class WorkflowState(TypedDict, total=False):
    workflow_stage: str
    next_step: str
    return_to: str
    status: str
    primary_intent: Optional[str]

class ExecutionState(TypedDict, total=False):
    refined_execution_plan: Optional[str]
    reasoning_summary: Optional[str]
    generated_sql: Optional[str]
    sql_error: Optional[str]
    query_results: Optional[List[Dict[str, Any]]]  # Actual DB rows returned (max 10)
    generated_insights: Optional[str]      # Unified string explanation container

class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    raw_user_query: Optional[str]
    uploaded_image: Optional[str]
    intent_classified: bool
    clarification: ClarificationState
    document: DocumentState
    workflow: WorkflowState
    execution: ExecutionState
    pending_clarification: Optional[Dict[str, Any]]

