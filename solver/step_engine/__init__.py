"""
Step-by-step solution engine for mathematical problems.

This module provides detailed, pedagogically structured solutions for:
- Algebra (linear and quadratic equations)
- Calculus (derivatives and integrals)
- Matrices (determinant, inverse, transpose, RREF, multiplication)

Usage:
    from solver.step_engine import build_steps
    
    steps = build_steps('2x + 5 = 15', 'solve', {'variable': 'x'})
    for step in steps:
        print(step.title)
        print(step.latex)
        print(step.explanation)
"""

from .base import Step, StepBuilder
from .algebra import AlgebraStepBuilder
from .calculus import DerivativeStepBuilder, IntegralStepBuilder
from .matrices import MatrixStepBuilder

__all__ = [
    'Step',
    'StepBuilder',
    'build_steps',
    'AlgebraStepBuilder',
    'DerivativeStepBuilder',
    'IntegralStepBuilder',
    'MatrixStepBuilder',
]


def build_steps(expression: str, operation: str, context: dict = None) -> list:
    """
    Build step-by-step solution for a given operation.
    
    Args:
        expression: Mathematical expression (e.g., "2x + 5 = 15", "x^2 + 3x")
        operation: Type of operation ('solve', 'derivative', 'integral', 'determinant', etc.)
        context: Additional context dict with parameters like 'variable', 'order', etc.
    
    Returns:
        List of Step objects
    
    Examples:
        # Solve equation
        steps = build_steps('2x + 5 = 15', 'solve', {'variable': 'x'})
        
        # Derivative
        steps = build_steps('x^2 + 3x', 'derivative', {'variable': 'x', 'order': 1})
        
        # Integral
        steps = build_steps('x^2', 'integral', {'variable': 'x', 'definite': False})
        
        # Matrix determinant
        steps = build_steps('[[1,2],[3,4]]', 'determinant')
    """
    if context is None:
        context = {}
    
    # Route to appropriate builder
    if operation == 'solve':
        builder = AlgebraStepBuilder()
        return builder.build_steps(expression, context)
    
    elif operation == 'derivative':
        builder = DerivativeStepBuilder()
        return builder.build_steps(expression, context)
    
    elif operation == 'integral':
        builder = IntegralStepBuilder()
        return builder.build_steps(expression, context)
    
    elif operation in ['determinant', 'inverse', 'transpose', 'rref', 'multiply']:
        builder = MatrixStepBuilder()
        context['operation'] = operation
        return builder.build_steps(expression, context)
    
    else:
        return [Step(
            title="Unknown operation",
            latex=operation,
            explanation=f"Operation '{operation}' is not supported."
        )]
