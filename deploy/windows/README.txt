TfeaterMathLab - Windows Deployment Packet
==========================================

Contents:
  install.bat              - One-time setup (venv, dependencies, migrate, collectstatic)
  run.bat                  - Start the development server
  launcher.py              - Python launcher (migrate + runserver + open browser)
  TfeaterMathLab.spec      - PyInstaller spec to build a Windows .exe
  BUILD_EXE.md             - How to build the .exe (run on Windows)
  set_env_local.bat.example - Copy to set_env_local.bat and set CEREBRAS_API_KEY etc.
  env_example.txt          - List of environment variables

Quick start:
  1. Open Command Prompt and cd to the project root (folder containing manage.py).
  2. Run:  deploy\windows\install.bat
  3. Copy set_env_local.bat.example to set_env_local.bat in this folder; edit and set CEREBRAS_API_KEY (optional).
  4. Run:  deploy\windows\run.bat
  5. Open http://127.0.0.1:8000/ in your browser.

Full instructions: see docs\DEPLOYMENT_WINDOWS.md
Building a standalone .exe: see BUILD_EXE.md (requires Windows + PyInstaller).
