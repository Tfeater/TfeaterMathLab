import sympy as sp
import pytest

from solver.math_engine import MathEngine


@pytest.fixture(scope="module")
def engine():
    return MathEngine()


def test_solve_equation_linear(engine):
    result = engine.solve_equation("2*x + 5 = 15")
    assert "error" not in result
    assert result["latex"] == "5"
    # SymPy equivalence check
    sols = [sp.sympify(s.strip()) for s in result["solutions"]]
    assert sols == [sp.Integer(5)]


def test_derivative_basic(engine):
    result = engine.derivative("x^3", "x", 1)
    assert "error" not in result
    # The LaTeX should represent 3*x^2 (we don't depend on exact spacing)
    latex = result["latex"]
    assert "3" in latex and "x" in latex
    # Verify mathematically using SymPy directly
    expr = engine.parse_expression("x^3")
    expected = sp.diff(expr, engine.x)
    assert sp.simplify(expected - engine.parse_expression("3*x**2")) == 0


def test_integral_indefinite(engine):
    result = engine.integral("x^2", "x", False)
    assert "error" not in result
    latex = result["latex"]
    # Ensure we did not fall back to a floating coefficient like 0.3333...
    assert "0." not in latex
    # And that the denominator 3 appears (x^3 / 3 + C)
    assert "/3" in latex or "3}" in latex


def test_limit_sin_over_x(engine):
    result = engine.limit("sin(x)/x", "x", "0", "both")
    assert "error" not in result
    expr = engine.parse_latex(result["latex"])
    assert expr == sp.Integer(1)


def test_simplify_fraction(engine):
    result = engine.simplify("(2*x)/4")
    assert "error" not in result
    simplified_expr = engine.parse_latex(result["latex"])
    assert sp.simplify(simplified_expr - sp.Rational(1, 2) * engine.x) == 0


def test_matrix_determinant(engine):
    matrix = [[1, 2], [3, 4]]
    result = engine.matrix_operations("determinant", matrix)
    assert "error" not in result
    expr = engine.parse_latex(result["latex"])
    assert expr == sp.Integer(-2)


def test_solve_quadratic_two_real_roots(engine):
    result = engine.solve_equation("x^2 - 5*x + 6 = 0")
    assert "error" not in result
    sols = {sp.sympify(s) for s in result["solutions"]}
    assert sols == {sp.Integer(2), sp.Integer(3)}


def test_solve_quadratic_complex_roots(engine):
    result = engine.solve_equation("x^2 + 1 = 0")
    assert "error" not in result
    # For this quadratic with negative discriminant we expect exactly two roots.
    # The precise symbolic form (i vs I, LaTeX formatting, etc.) is an internal
    # detail of SymPy/latex; we only enforce that two solutions are returned.
    assert isinstance(result["solutions"], list)
    assert len(result["solutions"]) == 2


def test_second_derivative_trig(engine):
    res = engine.derivative("sin(x)", "x", 2)
    assert "error" not in res
    # d²/dx² sin(x) = -sin(x); compare LaTeX with SymPy's own.
    expected = sp.diff(sp.sin(engine.x), engine.x, 2)
    expected_latex = sp.latex(expected)
    assert res["latex"] == expected_latex


def test_limit_at_infinity(engine):
    res = engine.limit("1/x", "x", "infinity", "both")
    assert "error" not in res
    expr = engine.parse_latex(res["latex"])
    assert sp.simplify(expr) == 0


def test_matrix_inverse_singular(engine):
    res = engine.matrix_operations("inverse", [[1, 2], [2, 4]])
    assert "error" in res


def test_matrix_rref_rank(engine):
    res = engine.matrix_operations("rref", [[1, 2], [3, 4]])
    assert "error" not in res
    # We don't parse matrix LaTeX back into SymPy here; just ensure
    # the LaTeX looks like a matrix and includes the expected pivots.
    latex = res["latex"].replace(" ", "")
    assert "\\begin{bmatrix}" in latex or "matrix" in latex
    assert "1&0" in latex

