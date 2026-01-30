"""
Base classes and utilities for step-by-step solution generation.

This module provides the foundation for all step engines, defining how
solutions are broken down into pedagogically meaningful steps.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod


@dataclass
class Step:
    """
    Represents a single step in a solution process.
    
    Attributes:
        title: Brief title describing what this step does
        latex: LaTeX expression for the mathematical content (no $ or $$ delimiters)
        explanation: Pedagogical description of why this step is valid
        formula: Optional named formula or rule being applied
        operation: Optional operation type (e.g., "distribute", "combine_like_terms")
    """
    title: str
    latex: str
    explanation: str
    formula: Optional[str] = None
    operation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class StepBuilder(ABC):
    """
    Abstract base class for building step-by-step solutions for specific domains.
    
    All step builders should:
    1. Parse the input expression into canonical form
    2. Generate deterministic, pedagogically ordered steps
    3. Return clean LaTeX (no embedded $ or $$)
    4. Provide clear explanations for each step
    """
    
    @abstractmethod
    def build_steps(self, expression: str, context: Dict[str, Any]) -> List[Step]:
        """
        Build a list of steps to solve or manipulate an expression.
        
        Args:
            expression: Mathematical expression (e.g., "2x + 5 = 15")
            context: Additional context like {'variable': 'x', 'result': '5'}
        
        Returns:
            List of Step objects ordered from start to final result
        
        Raises:
            ValueError: If expression is invalid or cannot be solved
        """
        pass
    
    def _format_latex(self, latex_str: str) -> str:
        """
        Clean LaTeX string by removing embedded $ or $$ delimiters.
        MathJax will wrap these in display/inline math automatically.
        """
        if not latex_str:
            return ""
        # Remove leading/trailing delimiters
        latex_str = latex_str.strip()
        if latex_str.startswith('$$') and latex_str.endswith('$$'):
            latex_str = latex_str[2:-2]
        elif latex_str.startswith('$') and latex_str.endswith('$'):
            latex_str = latex_str[1:-1]
        # Remove any interior $$ pairs
        latex_str = latex_str.replace('$$', '')
        # Remove any interior $ pairs but be careful not to break \$
        import re
        latex_str = re.sub(r'([^\\])\$', r'\1', latex_str)
        latex_str = re.sub(r'^\$', '', latex_str)
        return latex_str.strip()
