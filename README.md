# TfeaterMathLab

TfeaterMathLab is a Django‑based mathematics lab that combines a
deterministic SymPy engine with an AI explanation layer powered by the
Cerebras Cloud SDK. The goal is to provide step‑by‑step
solutions while preserving exact, symbolic results as the single source
of truth.

## Project structure

- `mathsolver/` – Django project configuration
  - `settings.py` – core Django settings and logging
  - `urls.py` – root URL configuration
- `solver/` – main application
  - `views.py` – HTTP endpoints (JSON APIs and HTML pages)
  - `urls.py` – app‑level URL routes
  - `models.py` – `Calculation`, `Graph`, and `UserProfile` models
  - `math_engine.py` – SymPy‑based deterministic math engine
  - `graph_generator.py` – Matplotlib‑based graph generation
  - `natural_parser.py` / `advanced_math_parser.py` – text to math parsing
  - `step_engine/` – rule‑based step generator for algebra, calculus, matrices
  - `step_serializer.py` – canonical step formatting
  - `services/ai_explainer.py` – AI explanation service (Cerebras)
  - `services/cerebras_text_solver.py` – AI text tab solver
  - `pdf_export.py` / `pdf_generator_reportlab.py` – PDF exports
  - `templates/solver/` – HTML templates for the UI
  - `static/docs/` – developer‑facing markdown documentation

## Running the project

### Prerequisites

- Python 3.11+ (3.12 tested)
- A Cerebras Cloud API key (for AI features; the core solver works without it)

### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set up environment variables:

```bash
export DJANGO_SECRET_KEY="your_dev_key"
export CEREBRAS_API_KEY="your_cerebras_api_key"
```

Run migrations and start the development server:

```bash
python manage.py migrate
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in a browser.

## Testing

The project uses `pytest` and `pytest‑django` for testing.

```bash
source venv/bin/activate
python -m pytest
```

Tests live under `solver/tests/` and cover:

- Core math engine operations
- API endpoints and fallback behavior
- Graph generation and PDF exports
- Error handling and structured fallback responses

## High‑level architecture

1. **Math engine (source of truth)**
   - All computations go through `MathEngine` in `math_engine.py`.
   - Outputs include a canonical symbolic result, LaTeX representation, and raw steps.
   - Fractions and symbolic forms are preserved whenever possible.

2. **AI explanation layer**
   - `ai_explainer.py` wraps Cerebras chat completions.
   - The engine’s final LaTeX result is passed in; the model is instructed to explain only.
   - The AI output is accepted only if its `final_answer.latex` is provably equivalent to the canonical SymPy result.

3. **Fallback to Text tab**
   - If parsing, evaluation, or runtime errors occur in any solver endpoint (except Text itself), a unified
     JSON fallback object is returned:

     ```json
     {
       "status": "fallback",
       "target_tab": "text",
       "original_input": "...",
       "error_type": "...",
       "error_message": "..."
     }
     ```

   - The frontend detects this and seamlessly redirects the user to the Text tab with the original input.

4. **Frontend rendering**
   - The main solver page (`index.html`) is a single‑page experience with tabs for algebra, calculus, matrices,
     graphing, and the Text solver.
   - LaTeX is rendered via MathJax.
   - Steps are rendered as a list of `{title, latex, explanation}` blocks.

5. **History and exports**
   - Each successful solve can be saved to `Calculation` history.
   - History is shown as a LaTeX‑rendered list with quick navigation back into the solver.
   - PDFs are generated from model data using ReportLab.

## Deployment notes

- The project uses SQLite by default and can be pointed to another database via `DATABASES` in `settings.py`.
- Static files, including documentation markdown under `solver/static/docs/`, are served using Django’s staticfiles
  configuration in development and should be collected and served via a proper static file server in production.

### Windows deployment packet

A Windows deployment packet with batch scripts and a manual is provided:

- **Scripts:** `deploy/windows/` — `install.bat` (one-time setup), `run.bat` (start server), `set_env_local.bat.example`, `env_example.txt`.
- **Manual:** [docs/DEPLOYMENT_WINDOWS.md](docs/DEPLOYMENT_WINDOWS.md) — step-by-step deployment and troubleshooting.

From the project root: run `deploy\windows\install.bat`, then configure `set_env_local.bat` (optional), then run `deploy\windows\run.bat`.

