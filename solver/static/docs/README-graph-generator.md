# Graph Generator (`graph_generator.py`)

The graph generator is responsible for turning validated mathematical
expressions into 2D plots using Matplotlib.

## Responsibilities

- Safely parse expressions into SymPy (`sympify` with a restricted local dictionary).
- Convert SymPy expressions into fast numerical functions via `lambdify`.
- Sample points over a numeric range and render a line plot.
- Return the resulting image as a base64‑encoded PNG string suitable for
  embedding in JSON responses and `<img>` tags.

## Key entry point

- `generate_plot(expression: str, x_range: Tuple[float, float], y_range: Optional[Tuple[float, float]], num_points: int = 1000) -> str`

Parameters:

- `expression` – a string such as `x^2`, `sin(x)`, or `exp(-x**2)`.
- `x_range` – numeric tuple `(x_min, x_max)`.
- `y_range` – optional numeric tuple `(y_min, y_max)` to clamp the vertical axis.
- `num_points` – resolution of the sample grid.

## Error handling

- Parsing or evaluation failures raise exceptions which bubble up to the
  `generate_graph` view.
- The view converts any such failure into a validation error and then a
  structured fallback JSON response pointing to the Text tab.
- No error text is drawn into the graph image itself; invalid inputs do
  not produce misleading graphs.

