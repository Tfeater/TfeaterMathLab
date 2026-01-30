# Frontend UI (`templates/solver/*.html`)

The frontend is rendered with plain HTML, CSS, and vanilla JavaScript,
with MathJax used for LaTeX rendering. The main entry point is
`templates/solver/index.html`.

## Main solver page (`index.html`)

- Provides a single‑page experience with tabs:
  - `Solve` – equation solving.
  - `Derivative` – derivatives.
  - `Integral` – integrals.
  - `Matrix` – matrix operations.
  - `Limit` – limits.
  - `Simplify`, `Factor`, `Expand` – algebraic transforms.
  - `Text` – AI‑powered text problem solving.
  - `Graph` – graphing tab.

- Shared elements:
  - Sticky header with navigation and theme toggle.
  - `tabConfig` JavaScript object that defines label, examples, and
    extra fields for each tab.
  - A single textarea input for the primary expression or text problem.
  - LaTeX preview area using MathJax.
  - Results section:
    - Final answer (`resultContent`).
    - Steps list (`stepsContent`) showing structured steps.
    - Optional explanation section for engine‑based explanations.
    - Export to PDF button.

## Text tab specifics

- Uses `/api/solve/text/` instead of `/api/solve/`.
- Expects the Cerebras JSON schema and maps it to:
  - A sequence of steps with titles, LaTeX, and explanations.
  - A final step labeled “Final step” that contains the final answer.
- Other explanation sections are hidden; the entire story is told
  through the linear steps list.

## Fallback behavior

- All non‑Text tabs inspect API responses:
  - If `{ "status": "fallback", "target_tab": "text", ... }` is present,
    the UI automatically:
    - Switches to the Text tab.
    - Fills the input with `original_input`.
    - Triggers a Text solve request.
    - Scrolls to the steps section.
- This makes syntax or engine errors feel like a seamless redirect to a
  more forgiving solver instead of a hard failure.

## History page (`history.html`)

- Uses `/api/history/` to fetch recent `Calculation` objects.
- Renders both expression and result using LaTeX (`\[…]`).
- Special‑cases Python‑style matrices like `[[1,2],[3,4]]` and formats
  them as LaTeX `bmatrix` expressions.
- Clicking a history item navigates back to the main solver with the
  original input ready to edit or rerun.

## About and Documentation pages

- Share the same theme (header, nav, theme toggle) as the main solver.
- About page focuses on:
  - Core philosophy (math first, AI second).
  - Key experiences and architecture overview.
- Documentation page focuses on:
  - Usage, tab behavior, syntax, and error handling.
  - Links to markdown developers’ documentation under `static/docs/`.

