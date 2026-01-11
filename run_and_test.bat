@echo off
cd "C:\Users\91902\OneDrive\Desktop\STAN NEW\chatbot_system"

echo Starting Luna server...
start /B .\venv\Scripts\uvicorn.exe web_server:app --host 0.0.0.0 --port 8000

timeout /t 10

echo Testing Luna...
.\venv\Scripts\python.exe test_luna.py

pause

