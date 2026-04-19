@echo off
echo ==============================
echo   NeuroLead Backend Startup
echo   Python 3.10
echo ==============================

cd /d "%~dp0"

REM Create .env if it doesn't exist
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env
)

REM Check if Python 3.10 venv exists, create it if not
if not exist .venv310 (
    echo Creating Python 3.10 virtual environment...
    py -3.10 -m venv .venv310
)

REM Activate the Python 3.10 venv
call .venv310\Scripts\activate.bat

REM Install / sync dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Confirm Python version
echo.
python --version

REM Start the server
echo.
echo Starting NeuroLead API server...
echo API Docs: http://localhost:8000/docs
echo ReDoc:    http://localhost:8000/redoc
echo Health:   http://localhost:8000/
echo.
python main.py
