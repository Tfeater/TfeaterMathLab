"""
TfeaterMathLab Windows launcher.
Run directly: python launcher.py
Or build as .exe with PyInstaller (see BUILD_EXE.md).
"""
import os
import sys
import webbrowser
import threading
import time

# Project root: when frozen (PyInstaller) use bundle dir; else parent of deploy/windows
if getattr(sys, "frozen", False):
    PROJECT_ROOT = sys._MEIPASS  # type: ignore[attr-defined]
else:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(_script_dir))

os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mathsolver.settings")

# Run Django runserver in a daemon thread so we can open the browser and wait
def run_server():
    import django
    django.setup()
    from django.core.management import execute_from_command_line
    execute_from_command_line(["manage.py", "runserver", "127.0.0.1:8000", "--noreload"])

def main():
    print()
    print("TfeaterMathLab")
    print("=============")
    print("Project root:", PROJECT_ROOT)
    print()

    import django
    django.setup()
    from django.core.management import call_command

    print("Running migrations...")
    try:
        call_command("migrate", "--noinput")
    except Exception as e:
        print("Migration warning:", e)
    print()

    print("Starting server at http://127.0.0.1:8000/")
    print("Browser will open shortly. Press Enter here to stop the server.")
    print()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000/")

    try:
        input("Press Enter to stop the server and exit... ")
    except (EOFError, KeyboardInterrupt):
        pass
    sys.exit(0)

if __name__ == "__main__":
    main()
