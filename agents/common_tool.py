from langchain_core.tools import tool

@tool
def db_config_tool() -> dict:
    """
    Returns database configuration from environment variables.
    Useful for agents that need DB access.
    """

    config = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
    }

    return config