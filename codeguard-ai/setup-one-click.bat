@echo off
setlocal

cd /d "%~dp0"
set "ROOT=%~dp0"

echo ========================================
echo      CodeGuard AI - One Click Setup
echo ========================================
echo.
echo Requirements for a new laptop:
echo - Node.js 18+
echo - Python 3.11+
echo.

where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed.
    echo Install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm is not available.
    echo Reinstall Node.js and make sure npm is selected.
    pause
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed.
    echo Install Python 3.11+ and enable "Add python.exe to PATH".
    pause
    exit /b 1
)

echo [1/6] Preparing backend environment...
cd backend

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo Created backend\.env from backend\.env.example
    ) else (
        echo WARNING: backend\.env.example not found. Backend will use default settings.
    )
)

if not exist "venv" (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create backend virtual environment.
        pause
        exit /b 1
    )
)

echo [2/6] Installing backend dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Backend dependency installation failed.
    pause
    exit /b 1
)

echo [3/6] Initializing backend database...
python init_db.py
if errorlevel 1 (
    echo ERROR: Database initialization failed.
    pause
    exit /b 1
)

cd ..\frontend

echo [4/6] Preparing frontend environment...
if not exist ".env.local" (
    echo NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1> ".env.local"
    echo Created frontend\.env.local
)

echo [5/6] Installing frontend dependencies...
npm install
if errorlevel 1 (
    echo ERROR: Frontend dependency installation failed.
    pause
    exit /b 1
)

cd ..

echo [6/6] Starting backend and frontend...
echo.
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.

start "CodeGuard Backend" cmd /k "cd /d ""%ROOT%backend"" && venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul
start "CodeGuard Frontend" cmd /k "cd /d ""%ROOT%frontend"" && npm run dev"

echo Setup complete. The app is starting in two new terminal windows.
echo Open http://localhost:3000 in your browser.
pause
