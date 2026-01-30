# Math Engine (`math_engine.py`)

The math engine is the deterministic core of TfeaterMathLab. It is built
on top of SymPy and is responsible for evaluating all symbolic
expressions and returning canonical results.

## Responsibilities

- Parse string and LaTeX expressions into SymPy objects.
- Solve algebraic equations (linear and quadratic by default).
- Compute derivatives (including higher‑order derivatives).
- Compute indefinite and definite integrals.
- Compute limits (including one‑sided and at infinity).
- Simplify, factor, and expand expressions.
- Perform matrix operations (determinant, inverse, transpose, RREF).
- Produce human‑readable results:
  - `result` – pretty string representation
  - `latex` – LaTeX expression without delimiters
  - `steps` – list of step descriptions (either from `step_engine` or simple LaTeX strings)

## Key entry points

- `solve_equation(equation: str) -> Dict`
- `derivative(expression: str, variable: str, order: int) -> Dict`
- `integral(expression: str, variable: str, definite: bool, lower: float, upper: float) -> Dict`
- `limit(expression: str, variable: str, point: str, side: str) -> Dict`
- `simplify(expression: str) -> Dict`
- `factor(expression: str) -> Dict`
- `expand(expression: str) -> Dict`
- `matrix_operations(operation: str, matrix_data: List[List]) -> Dict`

Each method returns a dictionary that is safe to serialize once passed
through `serialize_result_with_steps`.

## Parsing helpers

- `parse_expression(expression: str)` – parses plain‑text expressions like `2*x + 5` or `sin(x)/x`.
- `parse_latex(latex_str: str)` – parses LaTeX expressions such as `\\frac{x^2}{3}`.

Both methods prefer exact arithmetic (fractions, radicals) whenever
possible, and raise `ValueError` on parsing failures.

## Error handling

- Engine methods wrap most internal SymPy exceptions and return
  `{ "error": "<message>" }` to callers.
- View code (`views.solve`) is responsible for turning these into either
  HTTP errors or structured fallback responses for the Text tab.

