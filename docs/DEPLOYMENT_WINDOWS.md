# TfeaterMathLab — Windows Deployment Manual

This manual describes how to deploy and run **TfeaterMathLab** on Windows using the provided deployment packet.

---

## 1. Requirements

### 1.1 System

- **OS:** Windows 10 or Windows 11 (64-bit recommended).
- **Disk:** At least 500 MB free for the project and Python environment.
- **Browser:** Any modern browser (Chrome, Edge, Firefox) for accessing the app.

### 1.2 Software

- **Python 3.11 or 3.12** (3.12 recommended).
  - Download: [https://www.python.org/downloads/](https://www.python.org/downloads/)
  - During setup, enable **“Add Python to PATH”**.
  - Verify: open **Command Prompt** and run:
    ```bat
    python --version
    ```
    You should see something like `Python 3.12.x`.

- **Cerebras Cloud API key** (optional).
  - Required only for **AI features**: Text tab (natural-language math) and AI-generated explanations.
  - Get a key at: [https://cloud.cerebras.ai/](https://cloud.cerebras.ai/)
  - The rest of the app (algebra, calculus, matrices, graphs, PDF) works without it.

---

## 2. Deployment Packet Contents

The Windows deployment packet is in the folder **`deploy/windows/`**:

| File | Purpose |
|------|--------|
| **install.bat** | One-time setup: creates virtual environment, installs dependencies, runs migrations, collects static files. |
| **run.bat** | Starts the Django development server. |
| **launcher.py** | Python launcher (migrate + runserver + open browser). Can be run directly or packaged as .exe. |
| **TfeaterMathLab.spec** | PyInstaller spec file to build a standalone Windows .exe. |
| **BUILD_EXE.md** | How to build the .exe on Windows (requires PyInstaller). |
| **set_env_local.bat.example** | Example file for environment variables. You copy it to `set_env_local.bat` and edit. |
| **env_example.txt** | List and short description of all supported environment variables. |
| **README.txt** | Short quick-start summary. |

---

## 3. Step-by-Step Deployment

### Step 1: Unpack or clone the project

- Unzip the project (or clone the repository) to a folder, for example:
  - `C:\Projects\TfeaterMathLab`
- The project root must contain:
  - `manage.py`
  - `requirements.txt`
  - `mathsolver/`
  - `solver/`
  - `deploy/windows/`

### Step 2: Open Command Prompt in the project root

1. Press **Win + R**, type `cmd`, press Enter.
2. Go to the project folder, for example:
   ```bat
   cd /d C:\Projects\TfeaterMathLab
   ```
   Replace the path with your actual project path.

### Step 3: Run the installer

Run:

```bat
deploy\windows\install.bat
```

The script will:

1. Check that Python is available.
2. Create a virtual environment in `venv\` (if it does not exist).
3. Install dependencies from `requirements.txt`.
4. Run Django migrations (creates/updates `db.sqlite3`).
5. Collect static files into `staticfiles\`.

If any step fails, the script will show an error and pause. Fix the issue (e.g. install Python or fix PATH) and run `install.bat` again.

### Step 4: Configure environment variables (optional but recommended)

1. In **`deploy\windows\`**, copy the example file:
   - Copy **`set_env_local.bat.example`** and rename the copy to **`set_env_local.bat`**.
2. Open **`set_env_local.bat`** in Notepad (or another editor).
3. Set at least:
   - **CEREBRAS_API_KEY** — your Cerebras Cloud API key (for AI features).
   - For production, also set **DJANGO_SECRET_KEY** (and optionally **DJANGO_DEBUG=False**, **DJANGO_ALLOWED_HOSTS**).
4. Save the file.

**Important:** Do not commit `set_env_local.bat` to version control; it may contain secrets. It is listed in `.gitignore`.

### Step 5: Start the application

From the same project root in Command Prompt, run:

```bat
deploy\windows\run.bat
```

The script will:

- Change to the project root.
- Load variables from `deploy\windows\set_env_local.bat` if that file exists.
- Activate the virtual environment.
- Start the Django development server on **http://127.0.0.1:8000/**.

You should see something like:

```
Starting TfeaterMathLab at http://127.0.0.1:8000/
Press Ctrl+C to stop.
```

### Step 6: Open the application in a browser

1. Open a browser.
2. Go to: **http://127.0.0.1:8000/**
3. You should see the TfeaterMathLab home page. You can use:
   - **Algebra**, **Calculus**, **Matrices**, **Graph**, **Integral**, **Limit** tabs (work without Cerebras).
   - **Text** tab and AI explanations (require **CEREBRAS_API_KEY** in `set_env_local.bat`).

To stop the server, press **Ctrl+C** in the Command Prompt window.

---

## 4. Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| **DJANGO_SECRET_KEY** | Yes (production) | Secret key for Django; keep private. Defaults to a dev value if not set. |
| **DJANGO_DEBUG** | No | `True` or `False`. Use `False` in production. Default: `True`. |
| **DJANGO_ALLOWED_HOSTS** | No | Comma-separated list of allowed hosts, e.g. `localhost,127.0.0.1`. Default: `localhost,127.0.0.1`. |
| **CEREBRAS_API_KEY** | No (for AI) | Cerebras Cloud API key. Needed for Text tab and AI explanations. |

You can set these in **`set_env_local.bat`** (used by `run.bat`) or in Windows system environment variables.

---

## 5. Troubleshooting

### “Python is not recognized”

- Install Python from [python.org](https://www.python.org/downloads/) and during setup check **“Add Python to PATH”**.
- Restart Command Prompt after installation.
- If Python is installed but not in PATH, use the full path to `python.exe` in the batch files, or add Python’s folder to **System environment variables → Path**.

### “Virtual environment not found” when running run.bat

- Run **`deploy\windows\install.bat`** first from the project root. It creates the `venv` folder.

### “pip install” or “migrate” fails

- Ensure you are in the project root (folder containing `manage.py` and `requirements.txt`).
- Run Command Prompt as Administrator if you get permission errors (or install to a user-writable path).
- Check that the project folder is not read-only and is not under a synced cloud folder that might lock files.

### Text tab or AI explanations do not work

- Set **CEREBRAS_API_KEY** in **`set_env_local.bat`** (copy from `set_env_local.bat.example`).
- Restart **run.bat** after changing `set_env_local.bat`.
- Ensure the Cerebras API key is valid and has not been revoked.

### Port 8000 already in use

- Stop any other program using port 8000, or edit **`run.bat`** and change the last line to use another port, e.g.:
  ```bat
  python manage.py runserver 127.0.0.1:8001
  ```
  Then open **http://127.0.0.1:8001/** in the browser.

### Static files (CSS/JS) not loading

- Run again:
  ```bat
  deploy\windows\install.bat
  ```
  (it runs `collectstatic`).  
- Or manually:
  ```bat
  venv\Scripts\activate
  python manage.py collectstatic --noinput
  ```

---

## 6. Running Without the Batch Files

If you prefer to run commands yourself:

1. Open Command Prompt in the project root.
2. Activate the virtual environment:
   ```bat
   venv\Scripts\activate
   ```
3. Optionally set environment variables (or call `deploy\windows\set_env_local.bat`).
4. Start the server:
   ```bat
   python manage.py runserver 127.0.0.1:8000
   ```

---

## 7. Building a standalone .exe

You can build a Windows executable so users can run TfeaterMathLab **without installing Python**. The result is a folder containing `TfeaterMathLab.exe` that you can zip and distribute.

**Requirements:** Windows, Python 3.11+ with the project’s venv and dependencies installed, and PyInstaller (`pip install pyinstaller`).

**Steps (from project root in Command Prompt):**

1. Activate the virtual environment: `venv\Scripts\activate`
2. Install PyInstaller: `pip install pyinstaller`
3. Build: `pyinstaller deploy\windows\TfeaterMathLab.spec`
4. Output: `dist\TfeaterMathLab\` contains `TfeaterMathLab.exe` and supporting files. Zip that folder to distribute.

When users run the .exe, it will run migrations, start the server at http://127.0.0.1:8000/, and open the default browser. For Cerebras API key, they must set `CEREBRAS_API_KEY` (e.g. via a small .bat that sets it and runs the .exe). See **`deploy/windows/BUILD_EXE.md`** for details and one-file build options.

---

## 8. Production Notes

The deployment packet and this manual are aimed at **local or single-machine deployment** on Windows. For production:

- Use a proper WSGI server (e.g. **Gunicorn** or **Waitress**) instead of `runserver`.
- Set **DJANGO_DEBUG=False** and a strong **DJANGO_SECRET_KEY**.
- Set **DJANGO_ALLOWED_HOSTS** to your domain(s).
- Serve static files via a web server (e.g. IIS, Nginx) or a dedicated static file server.
- Use HTTPS and secure cookie/session settings (Django’s defaults when `DEBUG=False` help with this).
- Consider using a production database (e.g. PostgreSQL) instead of SQLite for multi-user or higher load.

For more about the project and development setup, see the root **README.md**. For building the Windows .exe, see **deploy/windows/BUILD_EXE.md**.
