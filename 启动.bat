@echo off
cd /d "%~dp0"
echo ================================================
echo   RAG Knowledge Base QA  -  starting...
echo   Browser: http://localhost:8501
echo   Close this window to stop the server
echo ================================================
".venv\Scripts\streamlit.exe" run app.py
pause