from backend.db import get_db_connection
import os
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("UPDATE trades SET status = 'closed', reasoning_text = reasoning_text || '\n\n[SYSTEM FORCE CLOSED GHOST TRADE]' WHERE status = 'open' AND asset_class = 'crypto'")
conn.commit()
conn.close()
print("Cleaned up ghost trades using native get_db_connection")
