@echo off
echo ========================================
echo         CodeGuard AI - Full Stack
echo ========================================
echo.
echo This will start both backend and frontend servers
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

echo.
echo Starting Backend Server...
echo.
start "CodeGuard Backend" cmd /k "cd backend && start.bat"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

echo.
echo Starting Frontend Server...
echo.
start "CodeGuard Frontend" cmd /k "cd frontend && start.bat"

echo.
echo ========================================
echo    Both servers are starting up!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Close this window or press any key to exit
pause > nul