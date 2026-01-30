# Building TfeaterMathLab Windows .exe

You can build a standalone Windows executable so users can run TfeaterMathLab without installing Python. The result is a **folder** containing `TfeaterMathLab.exe` and supporting files (one-folder build). You can zip that folder and distribute it.

---

## Requirements

- **Windows** (build must be done on Windows).
- **Python 3.11 or 3.12** with the project's virtual environment set up and all dependencies installed (`pip install -r requirements.txt`).
- **PyInstaller**: `pip install pyinstaller`

---

## Build steps

1. **Open Command Prompt** and go to the **project root** (the folder that contains `manage.py` and `deploy`).

2. **Activate the virtual environment** (if you use one):
   ```bat
   venv\Scripts\activate
   ```

3. **Install PyInstaller** (if not already installed):
   ```bat
   pip install pyinstaller
   ```

4. **Run the build**:
   ```bat
   pyinstaller deploy\windows\TfeaterMathLab.spec
   ```

5. **Output**: PyInstaller creates:
   - `dist\TfeaterMathLab\` — folder to distribute (contains `TfeaterMathLab.exe` and DLLs/data).
   - `build\` — temporary build files (can be deleted).

6. **Distribute**: Zip the folder `dist\TfeaterMathLab` and give it to users. They unzip, run `TfeaterMathLab.exe`, and the app will:
   - Run migrations (first run creates `db.sqlite3` in the same folder).
   - Start the server at http://127.0.0.1:8000/
   - Open the default browser to that URL.
   - Wait until the user presses Enter in the console to stop.

---

## Optional: one-file .exe

For a **single** `.exe` (no folder), edit `TfeaterMathLab.spec` and replace the end of the file (the `EXE` and `COLLECT` block) with a single `EXE` that includes everything:

```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TfeaterMathLab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

Then run `pyinstaller deploy\windows\TfeaterMathLab.spec` again. The result will be a single `dist\TfeaterMathLab.exe`. Note: first startup is slower (PyInstaller extracts to a temp folder) and some antivirus software may flag new one-file executables.

---

## Environment variables (Cerebras API key)

The .exe does **not** load `set_env_local.bat`. To use the Cerebras API (Text tab, AI explanations), users must set the environment variable **before** running the .exe:

- **Option A**: Create a small `run_TfeaterMathLab.bat` next to the .exe:
  ```bat
  set CEREBRAS_API_KEY=your_key_here
  TfeaterMathLab.exe
  ```
- **Option B**: Set `CEREBRAS_API_KEY` in Windows System Environment Variables (per user or system).

---

## Troubleshooting

- **"ModuleNotFoundError"** when running the .exe: add the missing module to `hiddenimports` in `TfeaterMathLab.spec`, then rebuild.
- **Database or static files**: The .exe uses the **current directory** as the project root when frozen (`_MEIPASS`). Migrations and `db.sqlite3` are created in the same folder as the .exe (or the temp folder for one-file builds).
- **Antivirus**: Some antivirus software may quarantine or block newly built .exe files. You may need to add an exception or use a one-folder build and sign the executable if distributing widely.
