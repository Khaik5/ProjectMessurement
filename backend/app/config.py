import os

import pyodbc
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "DefectAI P7 API"
API_PREFIX = "/api"


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


BACKEND_HOST = env("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(env("BACKEND_PORT", "8000"))
FRONTEND_URL = env("FRONTEND_URL", "http://localhost:5173")
JWT_SECRET_KEY = env("JWT_SECRET_KEY", "defectai_p7_super_secret_key")
JWT_ALGORITHM = env("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(env("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))


def get_sqlserver_connection():
    try:
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=DefectAI_P7_DB;"
            "UID=sa;"
            "PWD=123456;",
            timeout=5,
        )
        return conn
    except Exception as e:
        print("SQL Server connection error:", str(e))
        raise


def get_permission_connection():
    try:
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=PermissionDB;"
            "UID=sa;"
            "PWD=123456;",
            timeout=5,
        )
        return conn
    except Exception as e:
        print("PermissionDB connection error:", str(e))
        raise
