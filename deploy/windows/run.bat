@echo off
setlocal
title TfeaterMathLab - Development Server

:: Go to project root
cd /d "%~dp0..\.."

:: Load optional environment variables (same folder as this script)
if exist "%~dp0set_env_local.bat" (
    call "%~dp0set_env_local.bat"
)

:: Activate virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Run install.bat first.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

:: Defaults if not set by set_env_local.bat
if "%DJANGO_SETTINGS_MODULE%"=="" set DJANGO_SETTINGS_MODULE=mathsolver.settings

echo.
echo Starting TfeaterMathLab at http://127.0.0.1:8000/
echo Press Ctrl+C to stop.
echo.

python manage.py runserver 127.0.0.1:8000

pause
