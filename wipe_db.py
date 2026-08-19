from backend.db import get_db_connection
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("DELETE FROM trades")
conn.commit()
conn.close()
print("Database completely wiped using native connection.")
