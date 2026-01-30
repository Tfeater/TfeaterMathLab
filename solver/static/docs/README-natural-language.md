# Natural Language Parsing (`natural_parser.py`, `advanced_math_parser.py`)

The natural language parsing layer is responsible for turning user
phrases like “solve 2x + 5 equals 15” into canonical expressions and
operations the math engine can understand.

## `natural_parser.py`

Provides a thin wrapper that:

- Tokenizes simple English phrases.
- Detects operation keywords (solve, derivative, integral, limit, etc.).
- Extracts the core expression string.

Return format:

```json
{
  "operation": "solve",
  "expression": "2*x + 5 = 15"
}
```

If parsing fails, `None` is returned and the caller can decide how to
handle fallbacks (for example, redirecting to the Text tab).

## `advanced_math_parser.py`

Implements more sophisticated parsing helpers such as `parse_math_text`
for complex expressions where tokenization and normalization rules need
to be richer than the basic parser.

This module is used by the main solver views to:

- Handle variations in spacing and operator usage.
- Normalize input into the exact syntax expected by SymPy.

## Error handling and fallbacks

- The `parse_natural_language` view calls `NaturalLanguageParser().parse(text)`.
- If parsing fails or returns no result, the view returns a unified fallback
  JSON object instructing the frontend to redirect to the Text tab.

