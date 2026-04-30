from app.config import get_sqlserver_connection

try:
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DB_NAME()")
    print("Connected database:", cursor.fetchone()[0])
    conn.close()
except Exception as e:
    print("Connection failed:", e)
