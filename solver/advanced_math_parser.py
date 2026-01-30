"""
Advanced Math Parser - High-performance regex-based parser for mathematical expressions.
No external model dependencies - works instantly.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ProblemType(Enum):
    LINEAR_EQUATION = "linear_equation"
    QUADRATIC = "quadratic"
    SYSTEM = "system"
    DERIVATIVE = "derivative"
    INTEGRAL = "integral"
    LIMIT = "limit"
    SIMPLIFY = "simplify"
    FACTOR = "factor"
    EXPAND = "expand"
    MATRIX = "matrix"
    OTHER = "other"


@dataclass
class ParsedProblem:
    problem_type: ProblemType
    variables: List[str]
    equations: List[str]
    expression: str
    target: Dict[str, Any]
    domain: str
    confidence: float
    parsing_notes: List[str]


class AdvancedMathParser:
    """
    High-performance math parser using regex patterns and heuristic analysis.
    Handles Russian and English natural language math problems.
    """
    
    def __init__(self):
        # Math symbol replacements
        self.math_symbols = {
            '×': '*', '÷': '/', '·': '*', '−': '-',
            '²': '**2', '³': '**3', 'ⁿ': '**n',
            '√': 'sqrt', '∛': 'cbrt',
            'π': 'pi', '∞': 'oo',
        }
        
        # Keywords to remove
        self.stop_words = {
            # English
            'solve', 'find', 'calculate', 'compute', 'evaluate', 'simplify',
            'factor', 'expand', 'the', 'of', 'for', 'given', 'where', 'when', 'if',
            'derivative', 'integral', 'limit', 'with', 'respect', 'to',
            # Russian
            'реши', 'найди', 'вычисли', 'определи', 'упрости', 'разложи', 'раскрой',
            'уравнение', 'выражение', 'функции', 'функцию', 'для', 'при', 'от', 'до',
            'производная', 'производную', 'производной', 'интеграл', 'интеграла',
            'предел', 'предела', 'относительно', 'переменной',
        }
        
        self.parsing_cache = {}
    
    def parse(self, text: str) -> ParsedProblem:
        """Parse natural language math problem."""
        text = text.strip()
        
        if text in self.parsing_cache:
            return self.parsing_cache[text]
        
        result = self._parse_internal(text)
        self.parsing_cache[text] = result
        
        return result
    
    def _parse_internal(self, text: str) -> ParsedProblem:
        text_lower = text.lower()
        
        # Detect problem type
        problem_type, type_confidence = self._detect_problem_type(text_lower)
        
        # Extract variables
        variables = self._extract_variables(text)
        
        # Extract equations and expressions
        equations, expression = self._extract_equations_and_expressions(text)
        
        # Determine target
        target = self._determine_target(problem_type, text_lower, variables)
        
        # Determine domain
        domain = self._determine_domain(problem_type, text_lower)
        
        # Clean expression
        expression = self._clean_expression(expression)
        
        # Calculate confidence
        confidence = self._calculate_confidence(problem_type, type_confidence, equations, expression)
        
        return ParsedProblem(
            problem_type=problem_type,
            variables=variables,
            equations=equations,
            expression=expression,
            target=target,
            domain=domain,
            confidence=confidence,
            parsing_notes=[]
        )
    
    def _detect_problem_type(self, text: str) -> Tuple[ProblemType, float]:
        """Detect the type of math problem."""
        
        # Integral
        if any(kw in text for kw in ['integral', 'интеграл', 'int ']):
            if any(kw in text for kw in ['definite', 'определён', 'от ', 'from ']):
                return ProblemType.INTEGRAL, 0.95
            return ProblemType.INTEGRAL, 0.90
        
        # Derivative
        if any(kw in text for kw in ['derivative', 'd/dx', 'd/dy', 'd/d']):
            return ProblemType.DERIVATIVE, 0.95
        if any(kw in text for kw in ['производн']):  # Matches производная, производную, производной
            return ProblemType.DERIVATIVE, 0.95
        
        # Limit
        if any(kw in text for kw in ['limit', 'предел', 'lim ']):
            return ProblemType.LIMIT, 0.95
        
        # Quadratic
        if re.search(r'x\^2|x\*\*2|\bx2\b', text) or any(kw in text for kw in ['quadratic', 'квадратн']):
            if '=' in text:
                return ProblemType.QUADRATIC, 0.95
        
        # Linear equation
        if any(kw in text for kw in ['solve', 'реши', 'найди x', 'найди y']) and '=' in text:
            return ProblemType.LINEAR_EQUATION, 0.90
        
        # Operations
        if any(kw in text for kw in ['simplify', 'упрости']):
            return ProblemType.SIMPLIFY, 0.90
        if any(kw in text for kw in ['factor', 'разложи']):
            return ProblemType.FACTOR, 0.90
        if any(kw in text for kw in ['expand', 'раскрой']):
            return ProblemType.EXPAND, 0.90
        
        # Default equation detection
        if '=' in text:
            return ProblemType.LINEAR_EQUATION, 0.70
        
        return ProblemType.OTHER, 0.5
    
    def _extract_variables(self, text: str) -> List[str]:
        """Extract variables from text."""
        variables = set()
        text_lower = text.lower()
        
        # Single letter variables with word boundaries
        for var in 'xyzabctuvw':
            pattern = r'\b' + var + r'\b'
            if re.search(pattern, text_lower):
                variables.add(var)
        
        # Explicit "find x" patterns
        for var in 'xyz':
            if re.search(rf'(?:find|solve|для|for)\s+(?:the\s+)?{var}\b', text_lower):
                variables.add(var)
        
        return list(variables)
    
    def _extract_equations_and_expressions(self, text: str) -> Tuple[List[str], str]:
        """Extract equations and expressions from text."""
        equations = []
        expression = ""
        
        # Find equations with =
        eq_pattern = r'([^=\n]+)\s*=\s*([^=\n]+)'
        eq_matches = re.findall(eq_pattern, text)
        
        for eq in eq_matches:
            lhs = eq[0].strip()
            rhs = eq[1].strip()
            
            # Clean each side
            lhs_clean = self._extract_math_content(lhs)
            rhs_clean = self._extract_math_content(rhs)
            
            if lhs_clean and rhs_clean:
                equations.append(f"{lhs_clean} = {rhs_clean}")
        
        if not equations:
            expression = self._extract_math_content(text)
        else:
            expression = equations[0].split("=")[0].strip()
        
        return equations, expression
    
    def _extract_math_content(self, text: str) -> str:
        """Extract mathematical content from text."""
        # Remove stop words
        words = text.split()
        cleaned_words = []
        
        for word in words:
            word_clean = word.lower().rstrip('.,;:!?')
            if word_clean not in self.stop_words:
                cleaned_words.append(word)
        
        result = ' '.join(cleaned_words)
        
        # Clean up math symbols
        for old, new in self.math_symbols.items():
            result = result.replace(old, new)
        
        # Convert exponents
        result = re.sub(r'(\d+)\s*\^(\d+)', r'\1**\2', result)
        result = re.sub(r'(\w)\s*\^(\d+)', r'\1**\2', result)
        
        # Clean operators
        result = re.sub(r'\s*([*/+\-])\s*', r'\1', result)
        result = re.sub(r'\s*\(\s*', '(', result)
        result = re.sub(r'\s*\)\s*', ')', result)
        
        # Remove leading/trailing non-math characters
        result = re.sub(r'^[^\w*+/-]+', '', result)
        result = re.sub(r'[^\w*+/-]+$', '', result)
        
        return result
    
    def _clean_expression(self, expression: str) -> str:
        """Clean expression for SymPy."""
        if not expression:
            return ""
        
        expr = expression
        
        # Implicit multiplication: 2x -> 2*x
        expr = re.sub(r'(\d)([a-zA-Z(])', r'\1*\2', expr)
        expr = re.sub(r'([a-zA-Z0-9)])(\()', r'\1*\2', expr)
        
        # Convert functions
        expr = re.sub(r'\bsin\b', 'sin', expr)
        expr = re.sub(r'\bcos\b', 'cos', expr)
        expr = re.sub(r'\btan\b', 'tan', expr)
        expr = re.sub(r'\bln\b', 'log', expr)
        expr = re.sub(r'\blog\b(?!\w)', 'log', expr)
        expr = re.sub(r'\bexp\b', 'exp', expr)
        expr = re.sub(r'\bsqrt\b', 'sqrt', expr)
        
        # Clean dx, dy, etc.
        expr = re.sub(r'\s*d[a-z]\s*$', '', expr).strip()
        
        return expr
    
    def _determine_target(self, problem_type: ProblemType, text: str, variables: List[str]) -> Dict[str, Any]:
        """Determine the target/goal of the problem."""
        
        if problem_type in [ProblemType.LINEAR_EQUATION, ProblemType.QUADRATIC]:
            return {"solve_for": variables if variables else ['x']}
        
        elif problem_type == ProblemType.DERIVATIVE:
            var = variables[0] if variables else 'x'
            return {"find": "derivative", "variable": var, "order": 1}
        
        elif problem_type == ProblemType.INTEGRAL:
            var = variables[0] if variables else 'x'
            
            # Check for definite integral
            definite_match = re.search(r'(?:от|from)\s*([-\d.]+)\s*(?:до|to)\s*([-\d.]+)', text)
            if definite_match:
                from sympy import Rational
                return {
                    "find": "integral", "variable": var,
                    "definite": True,
                    "lower": Rational(definite_match.group(1)),
                    "upper": Rational(definite_match.group(2))
                }
            
            return {"find": "integral", "variable": var, "definite": False}
        
        elif problem_type == ProblemType.LIMIT:
            var = variables[0] if variables else 'x'
            point_match = re.search(r'(?:→|->|to|approaches?)\s*([^\s,]+)', text)
            point = point_match.group(1) if point_match else '0'
            return {"find": "limit", "variable": var, "point": point, "side": '+'}
        
        elif problem_type == ProblemType.SIMPLIFY:
            return {"find": "simplification"}
        elif problem_type == ProblemType.FACTOR:
            return {"find": "factorization"}
        elif problem_type == ProblemType.EXPAND:
            return {"find": "expansion"}
        
        return {}
    
    def _determine_domain(self, problem_type: ProblemType, text: str) -> str:
        """Determine the domain/field of mathematics."""
        
        if problem_type in [ProblemType.DERIVATIVE, ProblemType.INTEGRAL, ProblemType.LIMIT]:
            return "calculus"
        elif problem_type in [ProblemType.LINEAR_EQUATION, ProblemType.QUADRATIC,
                              ProblemType.SIMPLIFY, ProblemType.FACTOR, ProblemType.EXPAND]:
            return "algebra"
        
        return "algebra"
    
    def _calculate_confidence(self, problem_type: ProblemType, type_confidence: float,
                              equations: List[str], expression: str) -> float:
        """Calculate overall parsing confidence."""
        confidence = type_confidence
        
        if equations:
            confidence += 0.1
        if expression and len(expression) > 2:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def parse_to_dict(self, text: str) -> Dict[str, Any]:
        """Parse problem and return as dictionary."""
        result = self.parse(text)
        
        return {
            "problem_type": result.problem_type.value,
            "variables": result.variables,
            "equations": result.equations,
            "expression": result.expression,
            "target": result.target,
            "domain": result.domain,
            "confidence": result.confidence
        }


def parse_math_text(text: str) -> Dict[str, Any]:
    """Parse natural language math problem."""
    parser = AdvancedMathParser()
    return parser.parse_to_dict(text)


if __name__ == "__main__":
    parser = AdvancedMathParser()
    
    test_cases = [
        "Solve 2x + 5 = 15",
        "Реши уравнение: 3x - 7 = 2",
        "Find derivative of x^2 + 3x",
        "Найди производную x**2 + 4x",
        "Integral of x^2 dx",
        "Интеграл x^2 от 0 до 1",
        "Limit sin(x)/x as x approaches 0",
        "Предел sin(x)/x при x→0",
        "Simplify x^2 - 4",
        "Factor x^2 - 4",
        "Expand (x + 2)^2",
        "Solve x^2 + 5x + 6 = 0",
        "Find d/dx x^3 + 2x",
        "Вычисли предел 1/x при x→∞",
    ]
    
    print("=" * 60)
    print("Advanced Math Parser - Test Results")
    print("=" * 60)
    
    for test in test_cases:
        print(f"\nInput: {test}")
        print("-" * 40)
        result = parser.parse(test)
        print(f"Type: {result.problem_type.value}")
        print(f"Variables: {result.variables}")
        print(f"Expression: '{result.expression}'")
        print(f"Equations: {result.equations}")
        print(f"Target: {result.target}")
        print(f"Confidence: {result.confidence:.2f}")
