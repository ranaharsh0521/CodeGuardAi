@echo off
echo ========================================
echo    CodeGuard AI - Frontend Startup
echo ========================================
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo [1/2] Installing dependencies...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Please ensure Node.js 16+ is installed
        pause
        exit /b 1
    )
) else (
    echo [1/2] Dependencies found
)

echo [2/2] Starting development server...
echo.
echo ========================================
echo    Starting Next.js Development Server
echo ========================================
echo.
echo Frontend will be available at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the development server
npm run dev