@echo off
REM Zoho MCP Server Startup Script - Production Ready
REM Impact Realty AI Platform - All 7 endpoints

echo =========================================================
echo IMPACT REALTY - ZOHO MCP SERVER STARTUP
echo Production-grade server with all 7 endpoints
echo =========================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Dependencies installed successfully
echo.

REM Check for .env file
if not exist "..\..\..\..\.env" (
    echo WARNING: .env file not found at root level
    echo Please ensure ZOHO environment variables are set:
    echo   - ZOHO_CLIENT_ID
    echo   - ZOHO_CLIENT_SECRET
    echo   - ZOHO_REFRESH_TOKEN
    echo.
)

echo Starting Production Zoho MCP Server...
echo.
echo All 7 Endpoints Available:
echo   POST /mcp/zoho/dedupe
echo   POST /mcp/zoho/contact/create
echo   POST /mcp/zoho/deal/create
echo   POST /mcp/zoho/note/create
echo   POST /mcp/zoho/task/create
echo   POST /mcp/zoho/lead/convert
echo   POST /mcp/zoho/calendar/schedule
echo.
echo Server URLs:
echo   http://localhost:3001 (API)
echo   http://localhost:3001/docs (Swagger docs)
echo   http://localhost:3001/health (Health check)
echo.
echo Press Ctrl+C to stop the server
echo =========================================================

REM Start the server directly
python zoho_mcp_server.py

echo.
echo Server stopped.
pause