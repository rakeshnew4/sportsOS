@echo off
setlocal enabledelayedexpansion

cls
echo.
echo ==========================================
echo   [ok] SportsOS Phase 1-4 Demo Launcher
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found. Please install Python 3.10+
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [ok] %PYTHON_VERSION%

echo.
echo [+] Installing dependencies...
echo.

REM Install required packages
pip install -q fastapi uvicorn pydantic streamlit requests pandas firebase-admin

if errorlevel 1 (
    echo [FAIL] Failed to install dependencies
    exit /b 1
)

echo [ok] Dependencies installed

REM Create .streamlit/secrets.toml if it doesn't exist
if not exist ".streamlit\secrets.toml" (
    echo.
    echo [+] Creating .streamlit/secrets.toml...
    if not exist ".streamlit" mkdir .streamlit

    (
        echo # SportsOS API Configuration
        echo API_BASE_URL = "http://localhost:8000"
        echo DATA_BACKEND = "local_json"
        echo LOCAL_DATA_PATH = "./data/"
    ) > .streamlit\secrets.toml

    echo [ok] Created .streamlit/secrets.toml
)

echo.
echo ==========================================
echo   [+] Starting SportsOS Demo
echo ==========================================
echo.

echo [+] Starting FastAPI backend on http://localhost:8000...
echo.

REM Start backend in new window
start "SportsOS Backend" cmd /k "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak

echo.
echo [+] Starting Streamlit UI on http://localhost:8501...
echo.
echo ==========================================
echo   [ok] Ready to go!
echo ==========================================
echo.
echo   Frontend: http://localhost:8501
echo   Backend:  http://localhost:8000/docs
echo.
echo   Close this window to stop the app
echo ==========================================
echo.

REM Start Streamlit
streamlit run streamlit_app.py

pause
