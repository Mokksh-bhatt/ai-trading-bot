import sqlite3
conn = sqlite3.connect('backend/trades.db')
cursor = conn.cursor()
cursor.execute("SELECT SUM(realized_pnl) FROM trades WHERE status='closed'")
result = cursor.fetchone()[0]
print(f"Total Realized PnL: ${result:.2f}" if result else "Total Realized PnL: $0.00")
