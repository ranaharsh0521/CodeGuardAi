@echo off
echo ========================================
echo    CodeGuard AI - Backend Startup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Please ensure Python 3.8+ is installed
        pause
        exit /b 1
    )
) else (
    echo [1/4] Virtual environment found
)

REM Activate virtual environment
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
echo [3/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Initialize database
echo [4/4] Initializing database...
python init_db.py
if errorlevel 1 (
    echo WARNING: Database initialization failed, but continuing...
)

echo.
echo ========================================
echo    Starting FastAPI Server
echo ========================================
echo.
echo Backend will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
REM Reload mode uses Python multiprocessing on Windows and can fail with
REM "PermissionError: [WinError 5] Access is denied" in restricted folders.
if /I "%CODEGUARD_RELOAD%"=="1" (
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    uvicorn app.main:app --host 0.0.0.0 --port 8000
)
