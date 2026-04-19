@echo off
echo ==============================
echo   NeuroLead Backend Startup
echo ==============================

cd /d "%~dp0"

REM Create .env if it doesn't exist
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env
)

REM Check if venv exists
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Start the server
echo.
echo Starting NeuroLead API server...
echo API Docs: http://localhost:8000/docs
echo ReDoc:    http://localhost:8000/redoc
echo Health:   http://localhost:8000/
echo.
python main.py
