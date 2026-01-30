# Views and Routing (`views.py`, `urls.py`)

The views layer wires together HTTP endpoints, the math engine, AI
services, and templates to provide the full user experience.

## Routing

- `mathsolver/urls.py`:
  - Includes `solver.urls` at the root path.
- `solver/urls.py`:
  - `/` – main solver UI (`index` view).
  - `/about/` – About page.
  - `/documentation/` – Documentation page.
  - `/history/` – History page (auth‑protected).
  - `/profile/` – Profile page (auth‑protected).
  - `/api/solve/` – JSON API for algebra/calculus/matrix operations.
  - `/api/solve/text/` – JSON API for the AI text solver.
  - `/api/graph/` – JSON API for graph generation.
  - `/api/history/` – JSON API for user calculation history.
  - `/api/parse-natural/` – JSON API for natural language parsing.
  - `/api/export/pdf/...` – PDF export endpoints.

## Core API views

### `/api/solve/` – deterministic solver

- Expects JSON payload with:
  - `operation` – one of `solve`, `derivative`, `integral`, `limit`,
    `simplify`, `factor`, `expand`, `matrix`.
  - `expression` – math expression string.
  - Additional fields (`variable`, `order`, bounds, matrix options)
    depending on the operation.
- Dispatches to the appropriate `MathEngine` method.
- Normalizes results via `serialize_result_with_steps`.
- Optionally enriches with AI explanations from `ai_explainer` when the
  engine succeeds and the AI response is verified.
- On validation or runtime errors, returns a unified fallback JSON that
  instructs the frontend to redirect to the Text tab.

### `/api/solve/text/` – Text tab solver

- Accepts `{ "text": "word problem..." }`.
- Delegates to `cerebras_text_solver` and returns its structured JSON.
- Errors are returned as typed error objects; this endpoint does not
  emit fallback responses to avoid loops.

### `/api/graph/` – graph generation

- Parses `expression`, `x_min`, `x_max`, and optional `y` bounds.
- Calls `GraphGenerator.generate_plot`.
- On success, returns `{ "image": "<base64>" }`.
- On validation or runtime failure, returns the fallback JSON schema.

### `/api/history/`

- Returns the latest `Calculation` objects for the current user, with
  expressions, LaTeX, steps, and timestamps.

## HTML views

- `index` – main solver UI with tabs for all operations and the Text tab.
- `about` – themed About page describing the project.
- `documentation` – themed Documentation page summarizing usage and
  linking to markdown docs.
- `history` – paginated, LaTeX‑rendered calculation history.
- `profile` – user profile and theme preferences.

