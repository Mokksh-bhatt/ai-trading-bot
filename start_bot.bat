@echo off
echo ===================================================
echo   Starting AI Trading Observatory (Local System)
echo ===================================================
echo.

echo Launching Backend and Frontend in a single terminal window...
npx concurrently -k -p "[{name}]" -n "BACKEND,FRONTEND" -c "bgBlue.bold,bgMagenta.bold" "backend\venv\Scripts\uvicorn.exe backend.main:app --host 0.0.0.0 --port 8000" "npm run dev --prefix frontend"

pause
