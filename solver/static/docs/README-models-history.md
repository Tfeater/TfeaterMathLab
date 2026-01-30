# Models and History (`models.py`)

The `models.py` module defines the persistent data structures used
throughout the application.

## `Calculation`

Represents a single solved math problem.

- Fields (simplified):
  - `user` – optional foreign key to the Django `User`.
  - `operation_type` – string such as `solve`, `derivative`, `integral`.
  - `original_input` – raw text entered by the user.
  - `parsed_math_expression` – normalized expression used by SymPy.
  - `result` – human‑readable string result.
  - `latex_result` – LaTeX expression without delimiters.
  - `steps` – JSON field storing a list of serialized steps.
  - `created_at` – timestamp.

Used by:

- `/api/history/` to show recent calculations.
- PDF export views to build single or multi‑calculation documents.

## `Graph`

Represents a stored graph request.

- Fields (simplified):
  - `user` – foreign key to `User`.
  - `expression` – expression used for graphing.
  - `x_min`, `x_max`, `y_min`, `y_max` – numeric ranges.
  - `created_at` – timestamp.

Used by:

- History views and profile statistics (counts per user).

## `UserProfile`

Stores additional configuration per user.

- Fields:
  - `user` – one‑to‑one relation to `User`.
  - `theme_preference` – `light` or `dark`.

Used by:

- `profile` view and page to allow users to persist theme choices.

