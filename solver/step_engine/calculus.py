"""
Calculus step engine - generates detailed steps for derivatives and integrals.

Includes:
- Derivative rules: power, chain, product, quotient, exponential, trigonometric
- Integral rules: power, trigonometric, exponential, logarithmic
"""

from typing import List, Dict, Any, Optional
from .base import Step, StepBuilder
import sympy as sp
import re


class DerivativeStepBuilder(StepBuilder):
    """Builds step-by-step solutions for computing derivatives."""
    
    def build_steps(self, expression: str, context: Dict[str, Any]) -> List[Step]:
        """
        Build steps for computing a derivative.
        
        Args:
            expression: Function to differentiate, e.g., "x^2 + 3*x"
            context: Dict with 'variable' (default 'x') and optional 'order' (default 1)
        
        Returns:
            List of Step objects showing differentiation process
        """
        try:
            var_name = context.get('variable', 'x')
            order = context.get('order', 1)
            
            var = sp.Symbol(var_name)
            expr = sp.sympify(expression)
            
            steps = []
            
            # Step 1: State the problem
            if order == 1:
                steps.append(Step(
                    title="Find the derivative",
                    latex=f"\\frac{{d}}{{d{var_name}}} \\left({sp.latex(expr)}\\right)",
                    explanation=f"We need to find the derivative with respect to {var_name}.",
                    formula="Derivative notation: d/dx or f'(x)"
                ))
            else:
                steps.append(Step(
                    title=f"Find the {order}-order derivative",
                    latex=f"\\frac{{d^{order}}}{{d{var_name}^{order}}} \\left({sp.latex(expr)}\\right)",
                    explanation=f"We need to find the {order}-order derivative with respect to {var_name}.",
                    formula=f"Higher-order derivative: d^n/dx^n"
                ))
            
            # Analyze the expression structure
            rules_used = self._identify_rules(expr, var)
            
            # Add rules reference
            if rules_used:
                for rule_name, rule_formula in rules_used:
                    steps.append(Step(
                        title=f"Apply {rule_name}",
                        latex=rule_formula,
                        explanation=f"We can use the {rule_name} for this component.",
                        formula=rule_formula,
                        operation=f"apply_{rule_name.lower().replace(' ', '_')}"
                    ))
            
            # Compute derivative
            derivative = sp.diff(expr, var, order)
            simplified = sp.simplify(derivative)
            
            steps.append(Step(
                title="Compute derivative",
                latex=sp.latex(derivative),
                explanation=f"Apply the differentiation rules to get the derivative.",
                operation="compute"
            ))
            
            # Step: Simplify if different
            if simplified != derivative:
                steps.append(Step(
                    title="Simplify",
                    latex=sp.latex(simplified),
                    explanation="Simplify the result.",
                    operation="simplify"
                ))
            
            # Final result
            steps.append(Step(
                title="Final answer",
                latex=f"\\frac{{d^{order}f}}{{d{var_name}^{order}}} = {sp.latex(simplified)}",
                explanation=f"The {order}-order derivative is: {sp.latex(simplified)}",
                operation="solution"
            ))
            
            return steps
            
        except Exception as e:
            return [Step(
                title="Error computing derivative",
                latex=expression,
                explanation=f"Could not compute derivative: {str(e)}"
            )]
    
    def _identify_rules(self, expr: sp.Expr, var: sp.Symbol) -> List[tuple]:
        """
        Identify which derivative rules apply to this expression.
        
        Returns:
            List of (rule_name, rule_formula) tuples
        """
        rules = []
        
        # Check for different expression types
        expr_str = str(expr)
        
        # Power rule: d/dx[x^n] = n*x^(n-1)
        if any(str(arg).count('^') > 0 or isinstance(arg, sp.Pow) 
               for arg in sp.preorder_traversal(expr)):
            rules.append(("Power Rule", 
                         "\\frac{d}{dx}[x^n] = nx^{n-1}"))
        
        # Product rule: d/dx[u*v] = u'*v + u*v'
        if isinstance(expr, sp.Mul) and expr.has(var):
            args = [a for a in expr.args if a.has(var)]
            if len(args) > 1:
                rules.append(("Product Rule",
                             "\\frac{d}{dx}[u \\cdot v] = u' \\cdot v + u \\cdot v'"))
        
        # Quotient rule: d/dx[u/v] = (u'*v - u*v')/v^2
        if isinstance(expr, sp.Mul):
            for arg in expr.args:
                if isinstance(arg, sp.Pow) and arg.exp == -1:
                    rules.append(("Quotient Rule",
                                 "\\frac{d}{dx}\\left[\\frac{u}{v}\\right] = \\frac{u'v - uv'}{v^2}"))
                    break
        
        # Chain rule: d/dx[f(g(x))] = f'(g(x)) * g'(x)
        # Check for composed functions
        for node in sp.preorder_traversal(expr):
            if isinstance(node, (sp.sin, sp.cos, sp.tan, sp.exp, sp.log)) and node.has(var):
                rules.append(("Chain Rule",
                             "\\frac{d}{dx}[f(g(x))] = f'(g(x)) \\cdot g'(x)"))
                break
        
        # Trigonometric rules
        if expr.has(sp.sin) or expr.has(sp.cos) or expr.has(sp.tan):
            rules.append(("Trigonometric Rules",
                         "\\frac{d}{dx}[\\sin(x)] = \\cos(x), \\quad \\frac{d}{dx}[\\cos(x)] = -\\sin(x)"))
        
        # Exponential rule: d/dx[e^x] = e^x
        if expr.has(sp.exp):
            rules.append(("Exponential Rule",
                         "\\frac{d}{dx}[e^x] = e^x"))
        
        # Logarithmic rule: d/dx[ln(x)] = 1/x
        if expr.has(sp.log):
            rules.append(("Logarithmic Rule",
                         "\\frac{d}{dx}[\\ln(x)] = \\frac{1}{x}"))
        
        return rules


class IntegralStepBuilder(StepBuilder):
    """Builds step-by-step solutions for computing integrals."""
    
    def build_steps(self, expression: str, context: Dict[str, Any]) -> List[Step]:
        """
        Build steps for computing an integral.
        
        Args:
            expression: Integrand, e.g., "x^2 + 3*x"
            context: Dict with 'variable', 'definite' (bool), 'lower', 'upper'
        
        Returns:
            List of Step objects showing integration process
        """
        try:
            var_name = context.get('variable', 'x')
            is_definite = context.get('definite', False)
            lower = context.get('lower')
            upper = context.get('upper')
            
            var = sp.Symbol(var_name)
            expr = sp.sympify(expression)
            
            steps = []
            
            # Step 1: State the problem
            if is_definite:
                steps.append(Step(
                    title="Find the definite integral",
                    latex=f"\\int_{{{lower}}}^{{{upper}}} {sp.latex(expr)} \\, d{var_name}",
                    explanation=f"Compute the area under the curve from {lower} to {upper}.",
                    formula="Definite integral: ∫[a,b] f(x)dx"
                ))
            else:
                steps.append(Step(
                    title="Find the indefinite integral",
                    latex=f"\\int {sp.latex(expr)} \\, d{var_name}",
                    explanation=f"Find the antiderivative with respect to {var_name}.",
                    formula="Indefinite integral: ∫ f(x)dx = F(x) + C"
                ))
            
            # Analyze expression structure
            rules_used = self._identify_integration_rules(expr, var)
            
            # Add rules reference
            if rules_used:
                for rule_name, rule_formula in rules_used:
                    steps.append(Step(
                        title=f"Apply {rule_name}",
                        latex=rule_formula,
                        explanation=f"We can use the {rule_name} for this component.",
                        formula=rule_formula,
                        operation=f"apply_{rule_name.lower().replace(' ', '_')}"
                    ))
            
            # Compute antiderivative
            antiderivative = sp.integrate(expr, var)
            
            steps.append(Step(
                title="Find antiderivative",
                latex=sp.latex(antiderivative),
                explanation="Find a function whose derivative is the integrand.",
                operation="antiderivative"
            ))
            
            if not is_definite:
                steps.append(Step(
                    title="Final answer (indefinite integral)",
                    latex=f"{sp.latex(antiderivative)} + C",
                    explanation="Add the constant of integration C for indefinite integrals.",
                    formula="Constant of integration: ∫ f(x)dx = F(x) + C",
                    operation="solution"
                ))
            else:
                # Evaluate at bounds (symbolic, never float)
                at_upper = antiderivative.subs(var, upper)
                at_lower = antiderivative.subs(var, lower)
                # Rationalize intermediate values to avoid float representation
                at_upper_rationalized = sp.nsimplify(at_upper, rational=True)
                at_lower_rationalized = sp.nsimplify(at_lower, rational=True)
                result = at_upper_rationalized - at_lower_rationalized
                steps.append(Step(
                    title="Apply bounds",
                    latex=f"\\left[{sp.latex(antiderivative)}\\right]_{{{sp.latex(lower)}}}^{{{sp.latex(upper)}}}",
                    explanation=f"Evaluate the antiderivative at x = {sp.latex(upper)} and x = {sp.latex(lower)}.",
                    formula="Fundamental Theorem: [a,b] f(x)dx = F(b) - F(a)",
                    operation="apply_bounds"
                ))
                steps.append(Step(
                    title="Evaluate",
                    latex=f"{sp.latex(at_upper_rationalized)} - {sp.latex(at_lower_rationalized)} = {sp.latex(result)}",
                    explanation=f"Calculate F({sp.latex(upper)}) - F({sp.latex(lower)}).",
                    operation="evaluate"
                ))
                steps.append(Step(
                    title="Final answer (definite integral)",
                    latex=f"{sp.latex(result)}",
                    explanation=f"The area under the curve from {sp.latex(lower)} to {sp.latex(upper)} is {sp.latex(result)}.",
                    operation="solution"
                ))
            
            return steps
            
        except Exception as e:
            return [Step(
                title="Error computing integral",
                latex=expression,
                explanation=f"Could not compute integral: {str(e)}"
            )]
    
    def _identify_integration_rules(self, expr: sp.Expr, var: sp.Symbol) -> List[tuple]:
        """
        Identify which integration rules apply to this expression.
        
        Returns:
            List of (rule_name, rule_formula) tuples
        """
        rules = []
        
        # Power rule: ∫x^n dx = x^(n+1)/(n+1) + C
        if any(isinstance(arg, sp.Pow) for arg in sp.preorder_traversal(expr)):
            rules.append(("Power Rule",
                         "\\int x^n \\, dx = \\frac{x^{n+1}}{n+1} + C"))
        
        # Trigonometric rules
        if expr.has(sp.sin):
            rules.append(("Sine Integration",
                         "\\int \\sin(x) \\, dx = -\\cos(x) + C"))
        
        if expr.has(sp.cos):
            rules.append(("Cosine Integration",
                         "\\int \\cos(x) \\, dx = \\sin(x) + C"))
        
        # Exponential rule
        if expr.has(sp.exp):
            rules.append(("Exponential Integration",
                         "\\int e^x \\, dx = e^x + C"))
        
        # Logarithmic rule
        if expr.has(sp.log):
            rules.append(("Logarithmic Integration",
                         "\\int \\frac{1}{x} \\, dx = \\ln|x| + C"))
        
        # Sum rule: ∫(f+g) = ∫f + ∫g
        if isinstance(expr, sp.Add):
            rules.append(("Sum Rule",
                         "\\int (f(x) + g(x)) \\, dx = \\int f(x) \\, dx + \\int g(x) \\, dx"))
        
        # Constant multiple rule: ∫cf = c∫f
        if isinstance(expr, sp.Mul):
            rules.append(("Constant Multiple Rule",
                         "\\int c \\cdot f(x) \\, dx = c \\int f(x) \\, dx"))
        
        return rules
