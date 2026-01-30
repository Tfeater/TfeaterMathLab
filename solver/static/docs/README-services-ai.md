# AI Services (`services/ai_explainer.py`, `services/cerebras_text_solver.py`)

TfeaterMathLab integrates with the Cerebras Cloud SDK to provide
step‑by‑step explanations and a text‑driven solver. AI is always
secondary to the deterministic SymPy engine.

## AI Explanation Service (`ai_explainer.py`)

### Purpose

- Generate Symbolab‑style explanations for results already computed by
  the math engine.
- Accept or reject AI explanations based on whether their final answer
  matches the canonical SymPy result.

### Key concepts

- `AIExplanationService` wraps the Cerebras client, configured with
  `CEREBRAS_API_KEY` and model `llama-3.3-70b`.
- `generate_explanation(...)`:
  - Receives the original problem text, operation type, canonical LaTeX
    result, and optional internal steps from the engine.
  - Builds a prompt that clearly states the result is fixed and must not
    be changed.
  - Calls Cerebras chat completions with low temperature and no streaming.
  - Parses the JSON output into:

    ```python
    AIExplanationResult(
        steps=[AIExplanationStep(...)],
        final_answer_latex="..."
    )
    ```

- The view layer (`views.solve`) compares `final_answer_latex` to the
  engine’s `canonical_latex` using SymPy equivalence. If they do not
  match, it retries once with explicit correction context. If that fails
  again or times out, AI steps are discarded and engine steps are used
  instead.

### Error handling

- Raises `AIExplanationConfigError` when the API key or client setup is
  invalid.
- Raises `AIExplanationAPIError` for network or SDK‑level failures.
- Raises `AIExplanationResponseError` for malformed or non‑JSON answers.
- Callers catch these exceptions and fall back to deterministic behavior.

## Text Solver Service (`cerebras_text_solver.py`)

### Purpose

- Power the dedicated Text tab, which solves word problems and free‑form
  descriptions using Cerebras.

### Behavior

- Reads `CEREBRAS_API_KEY` and initializes a `Cerebras` client.
- Constructs prompts that instruct the model to:
  - Interpret a text problem.
  - Provide a structured, step‑by‑step JSON solution with:

    ```json
    {
      "problem": "...",
      "interpretation": "...",
      "steps": [
        { "step_number": 1, "description": "...", "latex": "..." }
      ],
      "final_answer": {
        "latex": "...",
        "explanation": "..."
      }
    }
    ```

  - Use LaTeX for all math, no markdown or extra prose.

- The `/api/solve/text/` endpoint forwards validated text to
  `cerebras_text_solver.solve_text_problem` and returns the structured JSON.

### Error handling

- Missing or invalid key: `CerebrasConfigError` with a clear message.
- Rate limits, malformed responses, or upstream issues are mapped to
  typed errors and returned as predictable JSON error objects for the
  frontend to display.

