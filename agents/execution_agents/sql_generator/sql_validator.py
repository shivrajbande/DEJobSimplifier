import json
from agents.common_tool import db_config_tool
from agents.state import AgentState

def sql_validator_node(state: AgentState):
    # 1. READ state attributes safely using consistent naming conventions
    exec_state = state.get("execution", {})
    clar_state = state.get("clarification", {})
    current_workflow = state.get("workflow", {})
    
    # Standardize on one tracking variable for code generation self-healing loops
    attempts = clar_state.get("clarification_attempt", 0)
    generated_sql = exec_state.get("generated_sql", "").strip()

    # Hard stop break to prevent runaway recursive token consumption
    if attempts >= 4:
        return {
            "workflow": {
                **current_workflow,
                "status": "failed",
                "next_step": "HITL_NODE",  # Explicitly fall back to human review on catastrophic failure
                "workflow_stage": "VALIDATION_FAILED_MAX_RETRIES"
            },
            "pending_clarification": {
                "selection_message": f"SQL validation failed after 4 self-healing attempts. Last Error: {exec_state.get('sql_error') or 'Unknown DB Error'}. Please clarify or correct your instructions.",
                "document_type": state.get("document", {}).get("document_type"),
                "sections": state.get("document", {}).get("extracted_sections", [])
            }
        }
    
    # 2. Structural DDL Execution Guardrails
    dangerous_commands = ['DROP DATABASE', 'TRUNCATE', 'DELETE FROM', 'PURGE', 'DROP TABLE']
    if any(cmd in generated_sql.upper() for cmd in dangerous_commands):
        return {
            "clarification": {
                **clar_state,
                "clarification_attempt": attempts + 1
            },
            "execution": {
                **exec_state,
                "sql_error": "Security Exception: High-risk operational keyword detected. You are only allowed to output standard SELECT statements, VIEWS, or MATERIALIZED VIEWS."
            },
            "workflow": {
                **current_workflow,
                "next_step": "SQL_GENERATOR_NODE",
                "workflow_stage": "GUARDRAIL_VIOLATION"
            }
        }
        
    # 3. Dynamic Syntax Validation Core
    try:
        validating_sql_query = f"EXPLAIN {generated_sql}"
        
        # Connect to MySQL using credentials and execute EXPLAIN
        import mysql.connector
        config = db_config_tool.func()
        
        # 1. Validate query syntax using EXPLAIN in an isolated connection
        conn_val = mysql.connector.connect(
            host=config.get("host"),
            port=config.get("port", 3306),
            user=config.get("user"),
            password=config.get("password"),
            database=config.get("database")
        )
        cur_val = conn_val.cursor(buffered=True)
        cur_val.execute(validating_sql_query)
        cur_val.fetchall() # Consumes EXPLAIN result set
        cur_val.close()
        conn_val.close()

        # 2. Execute the actual query to get real data for the insights generator in a new connection
        conn_exec = mysql.connector.connect(
            host=config.get("host"),
            port=config.get("port", 3306),
            user=config.get("user"),
            password=config.get("password"),
            database=config.get("database")
        )
        cur_exec = conn_exec.cursor(buffered=True)
        cur_exec.execute(generated_sql)
        columns = [col[0] for col in cur_exec.description] if cur_exec.description else []
        raw_rows = cur_exec.fetchmany(10)  # Max 10 rows
        query_results = [dict(zip(columns, row)) for row in raw_rows]
        cur_exec.close()
        conn_exec.close()
 
        # 100% Structural Validation Match Success! Pass forward safely.
        return {
            "clarification": {
                **clar_state,
                "clarification_attempt": 0,  # Reset attempts on success
                "clarification_needed": False  # Reset flag if any historical residue remains
            },
            "execution": {
                **exec_state,
                "query_results": query_results
            },
            "workflow": {
                **current_workflow,
                "next_step": "INSIGHTS_GENERATOR_NODE",
                "workflow_stage": "SQL_SYNTAX_VERIFIED"
            }
        }
 
    except Exception as mysql_error:
        print(f"❌ SQL Structural Validation Failed: {mysql_error}")
        return {
            "clarification": {
                **clar_state,
                "clarification_attempt": attempts + 1
            },
            "execution": {
                **exec_state,
                "sql_error": f"MYSQL_ERROR: {str(mysql_error)}"
            },
            "workflow": {
                **current_workflow,
                "next_step": "SQL_GENERATOR_NODE",
                "workflow_stage": "FIXING_SQL_SYNTAX"
            }
        }