@echo off
setlocal
title TfeaterMathLab - Windows Install

:: Go to project root (parent of deploy\windows)
cd /d "%~dp0..\.."

echo.
echo ============================================
echo   TfeaterMathLab - Windows Installation
echo ============================================
echo.
echo Project root: %CD%
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11 or 3.12 and add it to PATH.
    echo         Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

:: Create virtual environment if missing
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
    echo      Done.
) else (
    echo [1/4] Virtual environment already exists.
)
echo.

:: Activate venv and install dependencies
echo [2/4] Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo      Done.
echo.

:: Run migrations
echo [3/4] Running database migrations...
python manage.py migrate --noinput
if errorlevel 1 (
    echo [ERROR] migrate failed.
    pause
    exit /b 1
)
echo      Done.
echo.

:: Collect static files
echo [4/4] Collecting static files...
python manage.py collectstatic --noinput --clear
if errorlevel 1 (
    echo [WARN] collectstatic failed (non-fatal). You can run it again later.
) else (
    echo      Done.
)
echo.

echo ============================================
echo   Installation complete.
echo ============================================
echo.
echo Next steps:
echo   1. Copy set_env_local.bat.example to set_env_local.bat in this folder.
echo   2. Edit set_env_local.bat and set CEREBRAS_API_KEY (optional, for AI).
echo   3. Run run.bat to start the server.
echo.
pause
