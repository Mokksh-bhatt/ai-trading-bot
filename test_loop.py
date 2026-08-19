import asyncio
from backend.main import fast_execution_loop, SYMBOLS
print("Tracking:", SYMBOLS)
try:
    asyncio.run(asyncio.wait_for(fast_execution_loop(), timeout=10))
except Exception as e:
    pass
