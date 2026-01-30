"""
Math engine using SymPy for symbolic mathematics
"""
import sympy as sp
import re
from typing import Dict, List, Tuple, Optional

# Import step engine for detailed step-by-step solutions
try:
    from .step_engine import build_steps as build_steps_from_engine
except ImportError:
    build_steps_from_engine = None


class MathEngine:
    """Main math engine for solving various mathematical problems"""
    
    def __init__(self):
        self.x, self.y, self.z, self.t = sp.symbols('x y z t')
        self.symbols = {'x': self.x, 'y': self.y, 'z': self.z, 't': self.t}
    
    def _rationalize_result(self, result):
        """
        Convert float results to exact rational form where possible.
        This ensures fractions like -22/3 are shown instead of -7.333...
        """
        try:
            if isinstance(result, float):
                # Try to simplify float to rational
                return sp.nsimplify(result, rational=True)
            elif hasattr(result, 'evalf'):
                # For SymPy expressions that might be floats
                if isinstance(result, sp.Float):
                    return sp.nsimplify(result, rational=True)
            return result
        except:
            return result
    
    
    def get_detailed_explanation(self, operation: str, expression: str, 
                                  result: Dict, variable: str = 'x',
                                  definite: bool = False, lower: Optional[float] = None, 
                                  upper: Optional[float] = None, point: str = '0',
                                  side: str = '+') -> Dict:
        """Generate detailed step-by-step explanation with methods and rules used"""
        
        explanation = {
            'method': '',
            'description': '',
            'steps': [],
            'key_concepts': [],
            'formulas': [],
            'tips': []
        }
        
        if operation == 'solve':
            explanation = self._explain_solve(expression, result, variable)
        elif operation == 'derivative':
            explanation = self._explain_derivative(expression, result, variable)
        elif operation == 'integral':
            explanation = self._explain_integral(expression, result, variable, definite, lower, upper)
        elif operation == 'limit':
            explanation = self._explain_limit(expression, result, variable, point, side)
        elif operation == 'simplify':
            explanation = self._explain_simplify(expression, result)
        elif operation == 'factor':
            explanation = self._explain_factor(expression, result)
        elif operation == 'expand':
            explanation = self._explain_expand(expression, result)
        
        return explanation
    
    def _explain_solve(self, expression: str, result: Dict, variable: str) -> Dict:
        """Explain linear and quadratic equation solving"""
        explanation = {
            'method': 'Algebraic Equation Solving',
            'description': '',
            'steps': [],
            'key_concepts': [],
            'formulas': [],
            'tips': []
        }
        
        # Check if it's a quadratic equation
        if '**2' in expression or '^2' in expression or 'x^2' in expression.lower():
            explanation['method'] = 'Quadratic Equation Solution'
            explanation['description'] = 'This is a quadratic equation. We can solve it using the quadratic formula or by factoring.'
            explanation['key_concepts'] = [
                'Quadratic equation',
                'Quadratic formula',
                'Factoring',
                'Discriminant analysis'
            ]
            explanation['formulas'] = [
                f'For equation $ax^2 + bx + c = 0$:',
                '$x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$',
                'Discriminant $D = b^2 - 4ac$:',
                '- If $D > 0$: two real solutions',
                '- If $D = 0$: one real solution',
                '- If $D < 0$: two complex solutions'
            ]
            explanation['tips'] = [
                'Always rearrange the equation to standard form $ax^2 + bx + c = 0$ before solving',
                'Check your solutions by substituting back into the original equation',
                'The discriminant tells you about the nature of the roots'
            ]
        else:
            explanation['method'] = 'Linear Equation Solving'
            explanation['description'] = 'This is a linear equation. The goal is to isolate the variable on one side.'
            explanation['key_concepts'] = [
                'Linear equation',
                'Variable isolation',
                'Equivalence transformations'
            ]
            explanation['formulas'] = [
                'Basic operations: add/subtract same value from both sides',
                'Multiply/divide both sides by same non-zero value',
                'Golden rule: whatever you do to one side, do to the other'
            ]
            explanation['tips'] = [
                'Always perform the same operation on both sides',
                'Combine like terms before isolating the variable',
                'Check your answer by substituting back'
            ]
        
        explanation['steps'] = [
            {
                'title': 'Identify the equation',
                'description': f'Equation: ${expression}$',
                'formula': None
            },
            {
                'title': 'Rearrange to standard form',
                'description': 'Move all terms to one side to get the equation in standard form',
                'formula': None
            },
            {
                'title': 'Apply solution method',
                'description': f'Solving for {variable}',
                'formula': f'Result: ${result.get("latex", "")}$'
            },
            {
                'title': 'Verify solution',
                'description': 'Substitute the solution back to verify it satisfies the original equation',
                'formula': None
            }
        ]
        
        return explanation
    
    def _explain_derivative(self, expression: str, result: Dict, variable: str) -> Dict:
        """Explain derivative calculation with rules used"""
        explanation = {
            'method': 'Differentiation',
            'description': '',
            'steps': [],
            'key_concepts': [],
            'formulas': [],
            'tips': []
        }
        
        # Analyze expression to determine which rules apply
        has_power = bool(re.search(r'[a-zA-Z]\s*\^|pow\(', expression.lower()))
        has_trig = any(func in expression.lower() for func in ['sin', 'cos', 'tan', 'ln', 'log', 'exp'])
        has_chain = bool(re.search(r'\).*\(|\)\s*\(', expression))
        
        rules_used = []
        
        if has_power:
            rules_used.append('Power Rule')
        if has_trig:
            rules_used.append('Trigonometric/Exponential Rules')
        if has_chain:
            rules_used.append('Chain Rule')
        
        explanation['method'] = 'Derivative using: ' + ', '.join(rules_used) if rules_used else 'Differentiation'
        explanation['key_concepts'] = [
            'Derivative (rate of change)',
            'Instantaneous velocity',
            'Tangent slope'
        ]
        explanation['formulas'] = [
            'Power Rule: d/dx [x^n] = nx^(n-1)',
            'Chain Rule: d/dx [f(g(x))] = fprime(g(x)) * gprime(x)',
            'Product Rule: d/dx [uv] = uprime*v + u*vprime',
            'Quotient Rule: d/dx [u/v] = (uprime*v - u*vprime) / v^2',
            'd/dx [sin(x)] = cos(x)',
            'd/dx [cos(x)] = -sin(x)',
            'd/dx [ln(x)] = 1/x',
            'd/dx [e^x] = e^x'
        ]
        explanation['tips'] = [
            'Always identify the "outer" and "inner" functions for chain rule',
            'Apply power rule first, then other rules',
            'Don\'t forget to multiply by the derivative of the inside function'
        ]
        
        explanation['steps'] = [
            {
                'title': 'Identify the function',
                'description': f'Find derivative of $f({variable}) = {expression}$',
                'formula': None
            },
            {
                'title': 'Apply differentiation rules',
                'description': f'Using {", ".join(rules_used) if rules_used else "differentiation rules"}',
                'formula': f'$\\frac{{d}}{{d{variable}}} = {result.get("latex", "")}$'
            },
            {
                'title': 'Interpret the result',
                'description': f'The derivative tells us the instantaneous rate of change of the function at any point',
                'formula': None
            }
        ]
        
        return explanation
    
    def _explain_integral(self, expression: str, result: Dict, variable: str,
                          definite: bool, lower: Optional[float], upper: Optional[float]) -> Dict:
        """Explain integral calculation with methods used"""
        explanation = {
            'method': 'Integration',
            'description': '',
            'steps': [],
            'key_concepts': [],
            'formulas': [],
            'tips': []
        }
        
        has_power = bool(re.search(r'[a-zA-Z]\s*\^|pow\(', expression.lower()))
        has_trig = any(func in expression.lower() for func in ['sin', 'cos', 'tan', 'ln'])
        
        methods = []
        if has_power:
            methods.append('Power Rule for Integration')
        if has_trig:
            methods.append('Trigonometric Integration')
        if definite:
            methods.append('Fundamental Theorem of Calculus')
        
        explanation['method'] = 'Integration using: ' + ', '.join(methods) if methods else 'Integration'
        explanation['key_concepts'] = [
            'Antiderivative (indefinite integral)',
            'Definite integral (area under curve)',
            'Fundamental Theorem of Calculus'
        ]
        explanation['formulas'] = [
            'Power Rule: $\\int x^n dx = \\frac{x^{n+1}}{n+1} + C$ (for $n \\neq -1$)',
            '$\\int \\sin(x) dx = -\\cos(x) + C$',
            '$\\int \\cos(x) dx = \\sin(x) + C$',
            '$\\int e^x dx = e^x + C$',
            '$\\int \\frac{1}{x} dx = \\ln|x| + C$',
            'Fundamental Theorem: $\\int_a^b f(x) dx = F(b) - F(a)$',
            'Where $F$ is the antiderivative of $f$'
        ]
        explanation['tips'] = [
            'Integration is the inverse of differentiation',
            'Don\'t forget the constant of integration $C$ for indefinite integrals',
            'For definite integrals, evaluate at upper and lower limits and subtract',
            'When $n = -1$, use logarithmic integration'
        ]
        
        if definite:
            explanation['steps'] = [
                {
                    'title': 'Identify the definite integral',
                    'description': f'Find the area under the curve from ${lower}$ to ${upper}$',
                    'formula': f'$\\int_{{{lower}}}^{{{upper}}} {expression} \\, d{variable}$'
                },
                {
                    'title': 'Find the antiderivative',
                    'description': 'Apply integration rules to find the antiderivative',
                    'formula': f'$F({variable}) = {result.get("latex", "")}$ (without C for definite integral)'
                },
                {
                    'title': 'Apply Fundamental Theorem',
                    'description': f'Evaluate $F({upper}) - F({lower})$',
                    'formula': 'Using $\\int_a^b f(x) dx = F(b) - F(a)$'
                },
                {
                    'title': 'Calculate the result',
                    'description': 'The definite integral gives the net area between the curve and the x-axis',
                    'formula': None
                }
            ]
        else:
            explanation['steps'] = [
                {
                    'title': 'Identify the indefinite integral',
                    'description': f'Find the antiderivative of $f({variable}) = {expression}$',
                    'formula': f'$\\int {expression} \\, d{variable}$'
                },
                {
                    'title': 'Apply integration rules',
                    'description': 'Reverse differentiation to find the antiderivative',
                    'formula': f'$\\int {expression} \\, d{variable} = {result.get("latex", "")}$'
                },
                {
                    'title': 'Add constant of integration',
                    'description': 'Since this is indefinite, add $+C$ because derivative of constant is zero',
                    'formula': 'The constant represents an infinite family of antiderivatives'
                },
                {
                    'title': 'Verify by differentiation',
                    'description': 'Differentiate the result to get back the original function',
                    'formula': None
                }
            ]
        
        return explanation
    
    def _explain_limit(self, expression: str, result: Dict, variable: str, 
                       point: str, side: str) -> Dict:
        """Explain limit calculation with methods used"""
        explanation = {
            'method': 'Limit Evaluation',
            'description': '',
            'steps': [],
            'key_concepts': [],
            'formulas': [],
            'tips': []
        }
        
        explanation['key_concepts'] = [
            'Limit (approaching a value)',
            'One-sided limits',
            'Continuity',
            'Indeterminate forms'
        ]
        explanation['formulas'] = [
            '$\\lim_{x \\to a} f(x) = L$ means $f(x)$ approaches $L$ as $x$ approaches $a$',
            'Direct substitution: plug in $x = a$ if $f(a)$ is defined',
            '$\\frac{0}{0}$ or $\\frac{\\infty}{\\infty}$: indeterminate forms',
            "L'Hôpital's Rule: $\\lim \\frac{f}{g} = \\lim \\frac{f\\'}{g\\'}$ for $\\frac{0}{0}$ or $\\frac{\\infty}{\\infty}$",
            'One-sided limits: $x \\to a^+$ (from right) or $x \\to a^-$ (from left)'
        ]
        explanation['tips'] = [
            'Always try direct substitution first',
            'If you get $\\frac{0}{0}$, try factoring, L\'Hospital\'s rule, or algebraic manipulation',
            'Check if the function is continuous at the point',
            'One-sided limits help when function has different behavior from each side'
        ]
        
        # Determine which method likely applies
        is_standard = True
        if '0/0' in expression or 'indeterminate' in expression.lower():
            explanation['method'] = 'Limit with possible L\'Hospital\'s Rule'
        elif 'infinity' in expression.lower() or '∞' in expression:
            explanation['method'] = 'Limit at Infinity'
        else:
            explanation['method'] = 'Limit Evaluation'
        
        direction_text = 'from the right' if side == '+' else 'from the left'
        
        explanation['steps'] = [
            {
                'title': 'Set up the limit',
                'description': f'Evaluate $\\lim_{{{variable} \\to {point}}}$ {expression}',
                'formula': f'{direction_text} (${"+" if side == "+" else "-"}$)'
            },
            {
                'title': 'Try direct substitution',
                'description': f'Substitute ${variable} = {point}$ into the expression',
                'formula': 'Check if result is defined or indeterminate form'
            },
            {
                'title': 'Apply appropriate method',
                'description': 'If indeterminate, use factoring, conjugation, or L\'Hospital\'s rule',
                'formula': None
            },
            {
                'title': 'Calculate final value',
                'description': f'The limit value is: ${result.get("latex", "")}$',
                'formula': None
            }
        ]
        
        return explanation
    
    def _explain_simplify(self, expression: str, result: Dict) -> Dict:
        """Explain simplification process"""
        explanation = {
            'method': 'Algebraic Simplification',
            'description': '',
            'steps': [],
            'key_concepts': [],
            'formulas': [],
            'tips': []
        }
        
        explanation['key_concepts'] = [
            'Like terms',
            'Combining terms',
            'Reducing fractions',
            'Algebraic identities'
        ]
        explanation['formulas'] = [
            'Combine like terms: $ax + bx = (a+b)x$',
            'Factor out common factors',
            'Use identities like $a^2 - b^2 = (a-b)(a+b)$',
            'Simplify fractions by canceling common factors'
        ]
        explanation['tips'] = [
            'Always combine like terms first',
            'Look for common factors in numerator and denominator',
            'Use algebraic identities to simplify',
            'Check if further simplification is possible'
        ]
        
        explanation['steps'] = [
            {
                'title': 'Identify the expression',
                'description': f'Simplify: ${expression}$',
                'formula': None
            },
            {
                'title': 'Apply simplification rules',
                'description': 'Combine like terms, reduce fractions, apply identities',
                'formula': None
            },
            {
                'title': 'Verify the result',
                'description': 'Ensure the simplified form is equivalent to original',
                'formula': f'Result: ${result.get("latex", "")}$'
            }
        ]
        
        return explanation
    
    def _explain_factor(self, expression: str, result: Dict) -> Dict:
        """Explain factoring process"""
        explanation = {
            'method': 'Factoring',
            'description': '',
            'steps': [],
            'key_concepts': [],
            'formulas': [],
            'tips': []
        }
        
        explanation['key_concepts'] = [
            'Greatest Common Factor (GCF)',
            'Difference of squares',
            'Perfect square trinomials',
            'Factor by grouping'
        ]
        explanation['formulas'] = [
            'GCF: Factor out the largest common factor',
            'Difference of squares: $a^2 - b^2 = (a-b)(a+b)$',
            'Difference of cubes: $a^3 - b^3 = (a-b)(a^2 + ab + b^2)$',
            'Sum of cubes: $a^3 + b^3 = (a+b)(a^2 - ab + b^2)$',
            'Perfect square: $a^2 \\pm 2ab + b^2 = (a \\pm b)^2$'
        ]
        explanation['tips'] = [
            'Always factor out the GCF first',
            'Check the number of terms to determine the factoring method',
            'Verify by expanding the factored form',
            'For quadratics, find two numbers that multiply to ac and add to b'
        ]
        
        explanation['steps'] = [
            {
                'title': 'Identify the expression',
                'description': f'Factor: ${expression}$',
                'formula': None
            },
            {
                'title': 'Apply factoring techniques',
                'description': 'Use GCF, difference of squares, or other methods',
                'formula': None
            },
            {
                'title': 'Verify by expansion',
                'description': 'Multiply factors to check they give original expression',
                'formula': f'Result: ${result.get("latex", "")}$'
            }
        ]
        
        return explanation
    
    def _explain_expand(self, expression: str, result: Dict) -> Dict:
        """Explain expansion process"""
        explanation = {
            'method': 'Expansion',
            'description': '',
            'steps': [],
            'key_concepts': [],
            'formulas': [],
            'tips': []
        }
        
        explanation['key_concepts'] = [
            'Distributive property',
            'FOIL method',
            'Binomial expansion',
            'Pascal\'s triangle'
        ]
        explanation['formulas'] = [
            'Distributive: $a(b + c) = ab + ac$',
            'FOIL: $(a+b)(c+d) = ac + ad + bc + bd$',
            'Binomial theorem: $(a+b)^n = \\sum \\binom{n}{k} a^{n-k} b^k$',
            'Pascal\'s triangle for binomial coefficients'
        ]
        explanation['tips'] = [
            'Apply distributive property to each term',
            'Be careful with signs when expanding',
            'Combine like terms after expansion',
            'For powers, use binomial theorem or multiply step by step'
        ]
        
        explanation['steps'] = [
            {
                'title': 'Identify the expression',
                'description': f'Expand: ${expression}$',
                'formula': None
            },
            {
                'title': 'Apply distributive property',
                'description': 'Multiply each term in the first factor by each term in the second',
                'formula': 'Use FOIL or general distributive property'
            },
            {
                'title': 'Combine like terms',
                'description': 'Add or subtract terms with the same powers',
                'formula': f'Result: ${result.get("latex", "")}$'
            }
        ]
        
        return explanation
    
    def parse_latex(self, latex_str: str):
        """Parse LaTeX string to SymPy expression"""
        try:
            # Remove display math delimiters if present
            latex_str = latex_str.strip()
            if latex_str.startswith('$$') and latex_str.endswith('$$'):
                latex_str = latex_str[2:-2].strip()
            elif latex_str.startswith('$') and latex_str.endswith('$'):
                latex_str = latex_str[1:-1].strip()
            elif latex_str.startswith('\\[') and latex_str.endswith('\\]'):
                latex_str = latex_str[2:-2].strip()
            elif latex_str.startswith('\\(') and latex_str.endswith('\\)'):
                latex_str = latex_str[2:-2].strip()
            
            # Try to convert LaTeX to SymPy expression
            expr = self._latex_to_sympy(latex_str)
            return expr
        except Exception as e:
            raise ValueError(f"Error parsing LaTeX: {str(e)}")
    
    def _latex_to_sympy(self, latex_str: str):
        """Convert LaTeX to SymPy expression manually"""
        # Remove integral notation - already handled in views.py
        # Just clean up any remaining integral symbols
        latex_str = re.sub(r'\\int[^a-zA-Z]*', '', latex_str)
        # Remove d(var) notation if present
        latex_str = re.sub(r'\s*d[a-z]\s*$', '', latex_str)
        
        # Handle fractions first (most complex)
        def replace_frac(match):
            num = match.group(1)
            den = match.group(2)
            return f'({num})/({den})'
        
        latex_str = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', replace_frac, latex_str)
        
        # Handle nested fractions
        while '\\frac{' in latex_str:
            latex_str = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', replace_frac, latex_str)
        
        # Handle sqrt
        latex_str = re.sub(r'\\sqrt\[(\d+)\]\{([^}]+)\}', r'sqrt(\2, \1)', latex_str)
        latex_str = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', latex_str)
        
        # Handle subscripts before exponents (for limits, etc.)
        # Remove simple subscripts (keep for special cases like integrals which we handled)
        latex_str = re.sub(r'_\{([^}]+)\}(?!\^)', r'_\1', latex_str)
        
        # Handle exponents - need to be careful with nested braces
        def replace_exp(match):
            base = match.group(1)
            exp = match.group(2)
            return f'{base}**({exp})'
        
        latex_str = re.sub(r'(\w+)\^\{([^}]+)\}', replace_exp, latex_str)
        latex_str = re.sub(r'\)\^\{([^}]+)\}', r')**(\1)', latex_str)
        latex_str = re.sub(r'\}\^\{([^}]+)\}', r'**(\1)', latex_str)
        
        # Replace operators
        latex_str = latex_str.replace('\\cdot', '*')
        latex_str = latex_str.replace('\\times', '*')
        latex_str = latex_str.replace('\\div', '/')
        latex_str = latex_str.replace('\\pm', '+')
        latex_str = latex_str.replace('\\mp', '-')
        
        # Replace constants - do BEFORE function replacements to avoid conflicts
        latex_str = latex_str.replace('\\pi', 'pi')
        latex_str = latex_str.replace('\\e', 'e')
        latex_str = latex_str.replace('\\infty', 'infinity')
        latex_str = latex_str.replace('\\alpha', 'alpha')
        latex_str = latex_str.replace('\\beta', 'beta')
        latex_str = latex_str.replace('\\gamma', 'gamma')
        latex_str = latex_str.replace('\\theta', 'theta')
        
        # Replace functions AFTER constants to avoid conflicts (like ln in infinity)
        latex_str = latex_str.replace('\\sin', 'sin')
        latex_str = latex_str.replace('\\cos', 'cos')
        latex_str = latex_str.replace('\\tan', 'tan')
        latex_str = latex_str.replace('\\cot', 'cot')
        latex_str = latex_str.replace('\\sec', 'sec')
        latex_str = latex_str.replace('\\csc', 'csc')
        latex_str = latex_str.replace('\\ln', 'ln')
        latex_str = latex_str.replace('\\log', 'log')
        latex_str = latex_str.replace('\\exp', 'exp')
        latex_str = latex_str.replace('\\arcsin', 'asin')
        latex_str = latex_str.replace('\\arccos', 'acos')
        latex_str = latex_str.replace('\\arctan', 'atan')
        
        # Remove LaTeX delimiters
        latex_str = latex_str.replace('\\left(', '(')
        latex_str = latex_str.replace('\\right)', ')')
        latex_str = latex_str.replace('\\left[', '[')
        latex_str = latex_str.replace('\\right]', ']')
        latex_str = latex_str.replace('\\left|', 'abs(')
        latex_str = latex_str.replace('\\right|', ')')
        
        # Handle remaining backslashes (for Greek letters, etc.) - remove them
        latex_str = re.sub(r'\\([a-zA-Z]+)', r'\1', latex_str)
        
        # Handle simple exponent notation (x^2 style) - after other replacements
        latex_str = re.sub(r'(\w)\^(\d+)', r'\1**\2', latex_str)
        
        # Clean up special placeholders
        latex_str = latex_str.replace('INTEGRAL_DEF', 'integral_def')
        latex_str = latex_str.replace('INTEGRAL', 'integral')
        
        # Now parse as regular expression
        return self.parse_expression(latex_str)
    
    def parse_expression(self, expression: str):
        """Parse a string expression into a SymPy expression (handles both LaTeX and plain text)"""
        try:
            # Check if it looks like LaTeX
            if '\\' in expression or '{' in expression or '}' in expression:
                try:
                    return self.parse_latex(expression)
                except:
                    pass  # Fall through to regular parsing
            
            # Replace common function names
            expression = expression.replace('^', '**')
            expression = re.sub(r'(\d+)([xyz])', r'\1*\2', expression)  # 2x -> 2*x
            expression = re.sub(r'([xyz])(\d+)', r'\1**\2', expression)  # x2 -> x**2
            expression = re.sub(r'([xyz])\(', r'\1*(', expression)  # x( -> x*(
            expression = re.sub(r'\)([xyz])', r')*\1', expression)  # )x -> )*x
            expression = re.sub(r'\)\s*\(', ')*(', expression)  # )( -> )*(
            
            # Handle special integral placeholders before function replacement
            if 'integral_def(' in expression:
                # This is a definite integral placeholder - should not reach here in normal flow
                # But handle gracefully
                expression = expression.replace('integral_def', 'integral')
            
            # Replace function names - use sympy functions directly
            expression = expression.replace('sin', 'sin')
            expression = expression.replace('cos', 'cos')
            expression = expression.replace('tan', 'tan')
            expression = expression.replace('cot', 'cot')
            expression = expression.replace('sec', 'sec')
            expression = expression.replace('csc', 'csc')
            expression = expression.replace('ln', 'log')
            expression = expression.replace('log', 'log')
            expression = expression.replace('sqrt', 'sqrt')
            expression = expression.replace('exp', 'exp')
            expression = expression.replace('abs', 'Abs')
            
            # Handle Greek letters as symbols if needed
            expression = expression.replace('alpha', str(sp.Symbol('alpha')))
            expression = expression.replace('beta', str(sp.Symbol('beta')))
            expression = expression.replace('gamma', str(sp.Symbol('gamma')))
            expression = expression.replace('theta', str(sp.Symbol('theta')))
            expression = expression.replace('infinity', 'oo')
            
            # Evaluate safely
            safe_dict = {
                'x': self.x, 'y': self.y, 'z': self.z, 't': self.t,
                'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
                'cot': sp.cot, 'sec': sp.sec, 'csc': sp.csc,
                'log': sp.log, 'ln': sp.log, 'sqrt': sp.sqrt,
                'exp': sp.exp, 'Abs': sp.Abs, 'oo': sp.oo,
                '__builtins__': {},
                'e': sp.E,
                'pi': sp.pi,
            }
            
            # Try to parse with sympify first (safer)
            try:
                expr = sp.sympify(expression, locals=safe_dict)
                return expr
            except Exception as sympify_error:
                # Try more advanced parsing with custom handling
                try:
                    # Handle special cases that sympify might miss
                    if '^' in expression:
                        expression = expression.replace('^', '**')
                    
                    # Add implicit multiplication
                    expression = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', expression)
                    expression = re.sub(r'([a-zA-Z])(\d)', r'\1*\2', expression)
                    expression = re.sub(r'([a-zA-Z])([a-zA-Z\(])', r'\1*\2', expression)
                    
                    expr = sp.sympify(expression, locals=safe_dict)
                    return expr
                except Exception as e:
                    raise ValueError(f"Cannot parse expression: {expression}. Error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing expression: {str(e)}")
    
    def _get_step_engine_steps(self, operation: str, expression: str, context: Dict = None) -> List[Dict]:
        """
        Get detailed step-by-step solution from step_engine.
        
        Args:
            operation: 'solve', 'derivative', 'integral', 'determinant', etc.
            expression: Mathematical expression
            context: Additional context parameters
        
        Returns:
            List of step dictionaries with 'title', 'latex', 'explanation', etc.
        """
        if not build_steps_from_engine:
            return []
        
        if context is None:
            context = {}
        
        try:
            steps = build_steps_from_engine(expression, operation, context)
            # Convert Step objects to dictionaries
            return [step.to_dict() for step in steps]
        except Exception as e:
            # Fallback to empty steps if step_engine fails
            return []
    
    def solve_equation(self, equation: str) -> Dict:
        """Solve an equation"""
        try:
            # Handle = sign
            if '=' in equation:
                left, right = equation.split('=', 1)
                left_expr = self.parse_expression(left.strip())
                right_expr = self.parse_expression(right.strip())
                expr = left_expr - right_expr
            else:
                expr = self.parse_expression(equation)
                expr = sp.sympify(expr)
            
            # Solve
            solutions = sp.solve(expr, self.x)
            # Rationalize solutions
            solutions = [self._rationalize_result(sol) for sol in solutions]
            
            # Get detailed steps from step_engine
            detailed_steps = self._get_step_engine_steps('solve', equation, {'variable': 'x'})
            
            # Format steps in LaTeX (clean, no delimiters)
            expr_latex = sp.latex(expr)
            steps_latex = [
                f"Given: {expr_latex} = 0",
                f"Solving for x",
            ]
            
            if solutions:
                solutions_latex = ", ".join([sp.latex(sol) for sol in solutions])
                steps_latex.append(f"Solutions: {solutions_latex}")
                result_latex = solutions_latex
            else:
                steps_latex.append("No solution")
                result_latex = "\\text{No solution}"
            
            return {
                'result': ", ".join([sp.pretty(sol) for sol in solutions]) if solutions else "No solution",
                'latex': result_latex,
                'steps': detailed_steps if detailed_steps else steps_latex,
                'solutions': [sp.latex(sol) for sol in solutions] if solutions else []
            }
        except Exception as e:
            return {'error': str(e)}
    
    def derivative(self, expression: str, variable: str = 'x', order: int = 1) -> Dict:
        """Calculate derivative"""
        try:
            expr = self.parse_expression(expression)
            var = self.symbols.get(variable, self.x)
            
            # Get detailed steps from step_engine
            detailed_steps = self._get_step_engine_steps('derivative', expression, 
                                                         {'variable': variable, 'order': order})
            
            # Calculate derivative with steps in LaTeX (clean, no delimiters)
            expr_latex = sp.latex(expr)
            steps_latex = [f"f({variable}) = {expr_latex}"]
            
            current_expr = expr
            for i in range(order):
                current_expr = sp.diff(current_expr, var)
                prime_marks = "'" * (i + 1)
                deriv_latex = sp.latex(current_expr)
                steps_latex.append(f"f^{{{prime_marks}}}({variable}) = {deriv_latex}")
            
            return {
                'result': sp.pretty(current_expr),
                'latex': sp.latex(current_expr),
                'steps': detailed_steps if detailed_steps else steps_latex
            }
        except Exception as e:
            return {'error': str(e)}
    
    def integral(self, expression: str, variable: str = 'x', definite: bool = False, 
                 lower: Optional[float] = None, upper: Optional[float] = None) -> Dict:
        """Calculate integral"""
        try:
            expr = self.parse_expression(expression)
            var = self.symbols.get(variable, self.x)
            
            # Convert bounds to Rational for exact computation
            if lower is not None and upper is not None:
                lower_rational = sp.nsimplify(lower) if isinstance(lower, (int, float)) else lower
                upper_rational = sp.nsimplify(upper) if isinstance(upper, (int, float)) else upper
            
            # Get detailed steps from step_engine
            context = {
                'variable': variable,
                'definite': definite,
                'lower': lower,
                'upper': upper
            }
            detailed_steps = self._get_step_engine_steps('integral', expression, context)
            
            if definite and lower is not None and upper is not None:
                result = sp.integrate(expr, (var, lower_rational, upper_rational))
                # Rationalize the result to ensure exact fractions are shown
                result = self._rationalize_result(result)
                expr_latex = sp.latex(expr)
                steps_latex = [
                    f"\\int_{{{lower}}}^{{{upper}}} {expr_latex} d{variable}",
                    f"Evaluating from {lower} to {upper}...",
                    f"Result: {sp.latex(result)}"
                ]
                result_latex = sp.latex(result)
            else:
                result = sp.integrate(expr, var)
                # Add constant of integration C for indefinite integrals
                result_latex = sp.latex(result)
                # Check for standalone C (not part of \frac, etc.)
                if not re.search(r'(?<!\\)\b[Cc]\b', result_latex):
                    result_latex = f"{result_latex} + C"
                
                expr_latex = sp.latex(expr)
                steps_latex = [
                    f"\\int {expr_latex} d{variable}",
                    f"Indefinite integral: {result_latex}"
                ]
            
            return {
                'result': sp.pretty(result),
                'latex': result_latex,
                'steps': detailed_steps if detailed_steps else steps_latex
            }
        except Exception as e:
            return {'error': str(e)}
    
    def limit(self, expression: str, variable: str = 'x', point: str = '0', side: str = '+') -> Dict:
        """Calculate limit"""
        try:
            expr = self.parse_expression(expression)
            var = self.symbols.get(variable, self.x)
            
            # Parse point
            point_val = self.parse_expression(point)
            try:
                point_latex = sp.latex(point_val)
            except:
                point_latex = str(point)
            
            # Calculate limit
            if side == '+':
                result = sp.limit(expr, var, point_val)
            elif side == '-':
                result = sp.limit(expr, var, point_val, dir='-')
            else:
                result = sp.limit(expr, var, point_val)
            
            # Rationalize the result
            result = self._rationalize_result(result)
            
            steps_latex = [
                f"\\lim_{{{variable} \\to {point_latex}}} {sp.latex(expr)}",
                f"Result: {sp.latex(result)}"
            ]
            
            return {
                'result': sp.pretty(result),
                'latex': sp.latex(result),
                'steps': steps_latex
            }
        except Exception as e:
            return {'error': str(e)}
    
    def simplify(self, expression: str) -> Dict:
        """Simplify expression"""
        try:
            expr = self.parse_expression(expression)
            simplified = sp.simplify(expr)
            
            steps_latex = [
                f"Original: {sp.latex(expr)}",
                f"Simplified: {sp.latex(simplified)}"
            ]
            
            return {
                'result': sp.pretty(simplified),
                'latex': sp.latex(simplified),
                'steps': steps_latex
            }
        except Exception as e:
            return {'error': str(e)}
    
    def factor(self, expression: str) -> Dict:
        """Factor expression"""
        try:
            expr = self.parse_expression(expression)
            factored = sp.factor(expr)
            
            steps_latex = [
                f"Original: {sp.latex(expr)}",
                f"Factored: {sp.latex(factored)}"
            ]
            
            return {
                'result': sp.pretty(factored),
                'latex': sp.latex(factored),
                'steps': steps_latex
            }
        except Exception as e:
            return {'error': str(e)}
    
    def expand(self, expression: str) -> Dict:
        """Expand expression"""
        try:
            expr = self.parse_expression(expression)
            expanded = sp.expand(expr)
            
            steps_latex = [
                f"Original: {sp.latex(expr)}",
                f"Expanded: {sp.latex(expanded)}"
            ]
            
            return {
                'result': sp.pretty(expanded),
                'latex': sp.latex(expanded),
                'steps': steps_latex
            }
        except Exception as e:
            return {'error': str(e)}
    
    def matrix_operations(self, operation: str, matrix_data: List[List]) -> Dict:
        """Perform matrix operations"""
        try:
            # Convert string entries (like "1/2", "2") to SymPy expressions
            converted_matrix = []
            for row in matrix_data:
                converted_row = []
                for entry in row:
                    try:
                        # Try to parse as a SymPy expression (handles fractions, integers, symbols)
                        if isinstance(entry, str):
                            # Use Rational for fractions to maintain exact representation
                            if '/' in entry:
                                converted_row.append(sp.Rational(entry))
                            else:
                                # Try to parse as integer, symbol, or expression
                                val = sp.sympify(entry, rational=True)
                                converted_row.append(val)
                        else:
                            # Already numeric or symbolic
                            converted_row.append(entry)
                    except (ValueError, SyntaxError):
                        # If parsing fails, treat as symbol
                        converted_row.append(sp.Symbol(str(entry)))
                converted_matrix.append(converted_row)
            
            M = sp.Matrix(converted_matrix)
            
            # Get detailed steps from step_engine
            matrix_str = str(matrix_data).replace(' ', '')
            context = {'operation': operation}
            detailed_steps = self._get_step_engine_steps(operation, matrix_str, context)
            
            if operation == 'determinant':
                result = M.det()
                steps_latex = [f"Matrix: {sp.latex(M)}", f"Determinant: {sp.latex(result)}"]
            elif operation == 'inverse':
                result = M.inv()
                steps_latex = [f"Matrix: {sp.latex(M)}", f"Inverse: {sp.latex(result)}"]
            elif operation == 'transpose':
                result = M.T
                steps_latex = [f"Matrix: {sp.latex(M)}", f"Transpose: {sp.latex(result)}"]
            elif operation == 'rref':
                result, pivot_cols = M.rref()
                steps_latex = [f"Matrix: {sp.latex(M)}", f"RREF: {sp.latex(result)}"]
            else:
                return {'error': f"Unknown matrix operation: {operation}"}
            
            return {
                'result': sp.pretty(result),
                'latex': sp.latex(result),
                'steps': detailed_steps if detailed_steps else steps_latex
            }
        except Exception as e:
            return {'error': str(e)}
