@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"
set "LOG_DIR=%ROOT%logs"
set "BACKEND_URL=http://localhost:8000"
set "FRONTEND_URL=http://localhost:3000"

title CodeGuard AI - One Click Setup

echo ========================================
echo      CodeGuard AI - One Click Setup
echo ========================================
echo.
echo This script prepares and starts everything:
echo - Node.js and Python checks
echo - automatic Node.js/Python install with winget when available
echo - backend virtual environment
echo - backend .env from .env.example if missing
echo - Python dependencies
echo - database initialization
echo - frontend .env.local
echo - npm dependencies
echo - backend and frontend dev servers
echo.

if not exist "%BACKEND%" (
    echo ERROR: backend folder was not found.
    echo Run this file from the codeguard-ai folder.
    pause
    exit /b 1
)

if not exist "%FRONTEND%" (
    echo ERROR: frontend folder was not found.
    echo Run this file from the codeguard-ai folder.
    pause
    exit /b 1
)

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

call :FindPython
if errorlevel 1 exit /b 1

call :CheckPythonVersion
if errorlevel 1 exit /b 1

call :FindNode
if errorlevel 1 exit /b 1

call :CheckNodeVersion
if errorlevel 1 exit /b 1

call :FindNpm
if errorlevel 1 exit /b 1

echo [1/7] Preparing backend environment...
cd /d "%BACKEND%"

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo Created backend\.env from backend\.env.example
    ) else (
        echo WARNING: backend\.env.example not found. Create backend\.env if OAuth/API settings are needed.
    )
) else (
    echo backend\.env already exists
)

if not exist "venv\Scripts\python.exe" (
    echo Creating backend virtual environment...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create backend virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Backend virtual environment already exists
)

echo [2/7] Installing backend dependencies...
"%BACKEND%\venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo ERROR: Failed to upgrade backend packaging tools.
    pause
    exit /b 1
)

"%BACKEND%\venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Backend dependency installation failed.
    pause
    exit /b 1
)

echo [3/7] Initializing backend database...
"%BACKEND%\venv\Scripts\python.exe" init_db.py
if errorlevel 1 (
    echo ERROR: Database initialization failed.
    pause
    exit /b 1
)

echo [4/7] Preparing frontend environment...
cd /d "%FRONTEND%"

if not exist ".env.local" (
    > ".env.local" echo NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    echo Created frontend\.env.local
) else (
    echo frontend\.env.local already exists
)

echo [5/7] Installing frontend dependencies...
npm install
if errorlevel 1 (
    echo ERROR: Frontend dependency installation failed.
    pause
    exit /b 1
)

echo [6/7] Starting backend and frontend...
echo.
echo Backend:  %BACKEND_URL%
echo API Docs: %BACKEND_URL%/docs
echo Frontend: %FRONTEND_URL%
echo Logs:     %LOG_DIR%
echo.

start "CodeGuard AI Backend" cmd /k "cd /d ""%BACKEND%"" && ""%BACKEND%\venv\Scripts\python.exe"" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ""%LOG_DIR%\backend.log"" 2>&1"

echo Waiting for backend...
call :WaitForUrl "%BACKEND_URL%/docs" 30
if errorlevel 1 (
    echo Backend is still starting. If API does not work, check %LOG_DIR%\backend.log
) else (
    echo Backend is ready.
)

start "CodeGuard AI Frontend" cmd /k "cd /d ""%FRONTEND%"" && npm run dev > ""%LOG_DIR%\frontend.log"" 2>&1"

echo [7/7] Waiting for the app to become available...
call :WaitForUrl "%FRONTEND_URL%" 45
if errorlevel 1 (
    echo.
    echo The frontend is still starting.
    echo Open %FRONTEND_URL% after a few seconds.
    echo If it does not open, check:
    echo - %LOG_DIR%\frontend.log
    echo - %LOG_DIR%\backend.log
) else (
    echo Frontend is ready.
    start "" "%FRONTEND_URL%"
)

echo.
echo Setup complete.
echo Keep the backend and frontend terminal windows open while using the app.
echo.
pause
exit /b 0

:CheckNodeVersion
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 18 ? 0 : 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js 18+ is required.
    echo Install Node.js 18 or newer and run this setup again.
    pause
    exit /b 1
)
exit /b 0

:FindNode
where node >nul 2>&1
if not errorlevel 1 exit /b 0

echo Node.js was not found. Trying to install Node.js LTS with winget...
call :InstallWithWinget OpenJS.NodeJS.LTS "Node.js LTS"
if errorlevel 1 exit /b 1
call :RefreshToolPath

where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is still not available.
    echo Restart this computer, then double-click setup-one-click.bat again.
    pause
    exit /b 1
)
exit /b 0

:FindNpm
where npm >nul 2>&1
if not errorlevel 1 exit /b 0

echo npm was not found. Trying to install Node.js LTS with winget...
call :InstallWithWinget OpenJS.NodeJS.LTS "Node.js LTS"
if errorlevel 1 exit /b 1
call :RefreshToolPath

where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm is still not available.
    echo Restart this computer, then double-click setup-one-click.bat again.
    pause
    exit /b 1
)
exit /b 0

:FindPython
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    exit /b 0
)

echo Python was not found. Trying to install Python 3.11 with winget...
call :InstallWithWinget Python.Python.3.11 "Python 3.11"
if errorlevel 1 exit /b 1
call :RefreshToolPath

where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    exit /b 0
)

echo ERROR: Python is still not available.
echo Restart this computer, then double-click setup-one-click.bat again.
pause
exit /b 1

:CheckPythonVersion
%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.11+ is required.
    echo Install Python 3.11 or newer and run this setup again.
    pause
    exit /b 1
)
exit /b 0

:InstallWithWinget
where winget >nul 2>&1
if errorlevel 1 (
    echo ERROR: %~2 is required, and winget is not available for automatic install.
    echo Install it manually, then double-click setup-one-click.bat again.
    pause
    exit /b 1
)

winget install -e --id %~1 --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo ERROR: Failed to install %~2 with winget.
    echo Install it manually, then double-click setup-one-click.bat again.
    pause
    exit /b 1
)
exit /b 0

:RefreshToolPath
set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%LocalAppData%\Programs\Python\Python313;%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python311;%LocalAppData%\Microsoft\WindowsApps;%PATH%"
exit /b 0

:WaitForUrl
set "WAIT_URL=%~1"
set "WAIT_SECONDS=%~2"
set /a WAIT_COUNT=0

:WaitLoop
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -Uri '%WAIT_URL%' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 exit /b 0

set /a WAIT_COUNT+=1
if %WAIT_COUNT% GEQ %WAIT_SECONDS% exit /b 1
timeout /t 1 /nobreak >nul
goto WaitLoop
