from utils.embeddings import vector_db
from langchain_core.tools import tool

from langchain_core.tools import tool
import mysql.connector
from utils.config import get_env

@tool
def execute_sql_query_tool(sql_query: str, creds: dict):
    """
    Executes a SQL query using the provided credential dictionary.
    Returns the result rows or an error message.
    """
    config = {
        "host": get_env("DB_HOST"),
        "port": int(get_env("DB_PORT", 3306)),
        "user": get_env("DB_USER"),
        "password": get_env("DB_PASSWORD"),
        "database": get_env("DB_NAME"),
    }
    try:
        conn = mysql.connector.connect(
            host=config['host'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        cur = conn.cursor()
        cur.execute(sql_query)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return str(rows[:10])
    except Exception as e:
        return f"DB_ERROR: {str(e)}"