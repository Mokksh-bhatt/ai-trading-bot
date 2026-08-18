import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect('backend/trades.db')
cursor = conn.cursor()
today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
print(f"Filtering for date: {today}")

cursor.execute("SELECT SUM(realized_pnl) FROM trades WHERE status='closed' AND exit_time LIKE ?", (today + '%',))
result = cursor.fetchone()[0]

if result is not None:
    print(f"Today's Realized PnL: ${result:.2f}")
else:
    print("Today's Realized PnL: $0.00")
