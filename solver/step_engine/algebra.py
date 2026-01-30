"""
Algebra step engine - generates detailed steps for solving equations.

Supports:
- Linear equations: ax + b = c
- Quadratic equations: ax^2 + bx + c = 0
- Polynomial equations
"""

from typing import List, Dict, Any, Optional, Tuple
from .base import Step, StepBuilder
import sympy as sp
import re


class AlgebraStepBuilder(StepBuilder):
    """Builds step-by-step solutions for algebraic equations."""
    
    def __init__(self):
        self.variable = None
        self.lhs = None
        self.rhs = None
        self.equation = None
    
    def build_steps(self, expression: str, context: Dict[str, Any]) -> List[Step]:
        """
        Build steps for solving an algebraic equation.
        
        Args:
            expression: Equation string, e.g., "2x + 5 = 15"
            context: Dict with optional 'variable' (default 'x')
        
        Returns:
            List of Step objects from equation to solution
        """
        try:
            self.variable = context.get('variable', 'x')
            var = sp.Symbol(self.variable)
            
            # Parse equation - handle implicit multiplication
            expression = expression.strip()
            if '^' in expression:
                expression = expression.replace('^', '**')
            
            # Add implicit multiplication
            expression = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expression)
            expression = re.sub(r'([a-zA-Z])([a-zA-Z])', lambda m: m.group(0) if m.group(0) in ['sin', 'cos', 'tan', 'ln', 'log', 'exp'] else f"{m.group(1)}*{m.group(2)}", expression)
            
            # Parse equation
            if '=' not in expression:
                raise ValueError(f"Expected equation with '=' but got: {expression}")
            
            lhs_str, rhs_str = expression.split('=', 1)
            self.lhs = sp.sympify(lhs_str.strip())
            self.rhs = sp.sympify(rhs_str.strip())
            self.equation = sp.Eq(self.lhs, self.rhs)
            
            steps = []
            
            # Step 1: State the equation
            steps.append(Step(
                title="State the equation",
                latex=sp.latex(self.equation),
                explanation=f"We need to solve for {self.variable}. This is a linear/polynomial equation."
            ))
            
            # Step 2: Move all terms to one side if needed
            if self.rhs != 0:
                moved = self.lhs - self.rhs
                steps.append(Step(
                    title="Move all terms to left side",
                    latex=f"{sp.latex(moved)} = 0",
                    explanation=f"Subtract {sp.latex(self.rhs)} from both sides to get everything on one side.",
                    formula="Subtraction property of equality"
                ))
            
            # Step 3: Simplify/factor if possible
            poly = sp.Poly(self.lhs - self.rhs, var)
            degree = poly.degree()
            
            if degree == 1:
                # Linear equation
                steps.extend(self._solve_linear_steps(var, self.equation))
            elif degree == 2:
                # Quadratic equation
                steps.extend(self._solve_quadratic_steps(var, self.lhs - self.rhs))
            else:
                # Higher degree - use general solving
                steps.extend(self._solve_polynomial_steps(var, self.lhs - self.rhs))
            
            return steps
            
        except Exception as e:
            # Fallback: generic equation step
            return [Step(
                title="Error analyzing equation",
                latex=expression,
                explanation=f"Could not generate detailed steps: {str(e)}"
            )]
    
    def _solve_linear_steps(self, var: sp.Symbol, equation: sp.Eq) -> List[Step]:
        """Generate steps for solving linear equation ax + b = 0 (or ax + b = c)."""
        steps = []
        
        # Solve for variable
        solutions = sp.solve(equation, var)
        
        if not solutions:
            return [Step(
                title="No solution",
                latex="\\text{No solution}",
                explanation="This equation has no solution."
            )]
        
        solution = solutions[0]
        
        # Show solving process based on equation structure
        lhs, rhs = equation.lhs, equation.rhs
        
        # Collect coefficients
        a, b = sp.fraction(lhs - rhs)  # Get numerator and denominator
        collected = sp.collect(lhs - rhs, var)
        
        # Try to break down the solution steps
        # For ax + b = c, steps are: ax + b = c -> ax = c - b -> x = (c - b) / a
        
        if isinstance(collected, sp.Add):
            # Extract coefficient of var and constant
            coeff_var = collected.coeff(var, 1)
            const = collected.coeff(var, 0)
            
            if coeff_var is not None and const is not None:
                # Step: Isolate variable term
                isolated_const = -const
                steps.append(Step(
                    title="Isolate variable term",
                    latex=f"{sp.latex(var)} \\cdot {sp.latex(coeff_var)} = {sp.latex(isolated_const)}",
                    explanation=f"Move the constant {sp.latex(const)} to the other side by subtracting from both sides.",
                    formula="Addition/Subtraction property of equality"
                ))
                
                # Step: Divide both sides
                if coeff_var != 1:
                    steps.append(Step(
                        title="Divide both sides",
                        latex=f"{sp.latex(var)} = \\frac{{{sp.latex(isolated_const)}}}{{{sp.latex(coeff_var)}}}",
                        explanation=f"Divide both sides by {sp.latex(coeff_var)} to isolate {self.variable}.",
                        formula="Division property of equality"
                    ))
        
        # Step: Final solution
        steps.append(Step(
            title="Solution",
            latex=f"{self.variable} = {sp.latex(solution)}",
            explanation=f"Therefore, {self.variable} = {sp.latex(solution)}",
            operation="solution"
        ))
        
        return steps
    
    def _solve_quadratic_steps(self, var: sp.Symbol, expr: sp.Expr) -> List[Step]:
        """Generate steps for solving quadratic equation ax^2 + bx + c = 0."""
        steps = []
        
        # Try to factor
        factored = sp.factor(expr)
        
        if factored != expr:  # Successfully factored
            steps.append(Step(
                title="Factor the quadratic",
                latex=f"{sp.latex(factored)} = 0",
                explanation="Look for factors of the quadratic expression.",
                formula="Quadratic factoring"
            ))
            
            # Extract factors
            factors = sp.factor_list(expr)[1]
            for factor, mult in factors:
                if mult == 1 and factor != 1:
                    root = sp.solve(factor, var)
                    if root:
                        steps.append(Step(
                            title=f"Set factor {sp.latex(factor)} = 0",
                            latex=f"{self.variable} = {sp.latex(root[0])}",
                            explanation=f"Using the zero product property, {sp.latex(factor)} = 0",
                            formula="Zero product property"
                        ))
        else:
            # Use quadratic formula
            solutions = sp.solve(expr, var)
            
            # Extract a, b, c from ax^2 + bx + c = 0
            poly = sp.Poly(expr, var)
            coeffs = poly.all_coeffs()
            
            if len(coeffs) >= 3:
                a, b, c = coeffs[0], coeffs[1], coeffs[2]
                
                steps.append(Step(
                    title="Apply quadratic formula",
                    latex=f"{self.variable} = \\frac{{-{sp.latex(b)} \\pm \\sqrt{{{sp.latex(b**2 - 4*a*c)}}}}}{{2 \\cdot {sp.latex(a)}}}",
                    explanation=f"For ax² + bx + c = 0, use: x = (-b ± √(b² - 4ac)) / 2a",
                    formula="Quadratic formula: x = (-b ± √(b² - 4ac)) / 2a"
                ))
        
        # Final solutions
        solutions = sp.solve(sp.Eq(expr, 0), var)
        for i, sol in enumerate(solutions, 1):
            steps.append(Step(
                title=f"Solution {i}" if len(solutions) > 1 else "Solution",
                latex=f"{self.variable} = {sp.latex(sol)}",
                explanation=f"{self.variable} = {sp.latex(sol)}",
                operation="solution"
            ))
        
        return steps
    
    def _solve_polynomial_steps(self, var: sp.Symbol, expr: sp.Expr) -> List[Step]:
        """Generate steps for solving higher-degree polynomial equations."""
        steps = []
        
        # Try factoring first
        factored = sp.factor(expr)
        if factored != expr:
            steps.append(Step(
                title="Factor the polynomial",
                latex=f"{sp.latex(factored)} = 0",
                explanation="Attempt to factor the polynomial expression.",
                formula="Polynomial factoring"
            ))
        
        # Solve for all roots
        solutions = sp.solve(expr, var)
        
        if solutions:
            for i, sol in enumerate(solutions, 1):
                steps.append(Step(
                    title=f"Solution {i}" if len(solutions) > 1 else "Solution",
                    latex=f"{self.variable} = {sp.latex(sol)}",
                    explanation=f"One solution is {self.variable} = {sp.latex(sol)}",
                    operation="solution"
                ))
        else:
            steps.append(Step(
                title="Cannot solve",
                latex="\\text{No solutions found}",
                explanation="This polynomial equation is difficult to solve analytically."
            ))
        
        return steps
