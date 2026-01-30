"""
Step Serialization Layer

Ensures that step-by-step solutions are properly serialized for:
1. Frontend rendering (JSON)
2. PDF generation (clean data)
3. History storage (database)

This module defines the canonical step format that flows through
the entire application.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict


class StepSerializer:
    """
    Converts step objects and step lists to a canonical JSON-serializable format.
    
    This ensures ONE canonical representation of steps that is:
    - Frontend-safe (no raw objects)
    - PDF-ready (proper structure)
    - Database-safe (clean primitives)
    """
    
    @staticmethod
    def serialize_step(step: Any) -> Dict[str, str]:
        """
        Convert any step representation to canonical dict format.
        
        Args:
            step: Can be:
                - Step dataclass object
                - dict with step fields
                - string (fallback: treated as latex)
        
        Returns:
            Dict with keys: title, latex, explanation (all strings)
            Removes internal fields like operation, formula
        
        Raises:
            ValueError: If step cannot be serialized
        """
        if isinstance(step, str):
            # Fallback for legacy string format
            return {
                'title': 'Step',
                'latex': step.strip(),
                'explanation': ''
            }
        
        if isinstance(step, dict):
            # Already a dict - extract required fields
            return {
                'title': str(step.get('title', 'Step')).strip(),
                'latex': str(step.get('latex', '')).strip(),
                'explanation': str(step.get('explanation', '')).strip()
            }
        
        # Handle dataclass objects (Step from step_engine)
        if hasattr(step, '__dataclass_fields__'):
            step_dict = asdict(step) if callable(asdict) else vars(step)
            return {
                'title': str(step_dict.get('title', 'Step')).strip(),
                'latex': str(step_dict.get('latex', '')).strip(),
                'explanation': str(step_dict.get('explanation', '')).strip()
            }
        
        # Handle objects with expected attributes
        if hasattr(step, 'title') and hasattr(step, 'latex'):
            return {
                'title': str(getattr(step, 'title', 'Step')).strip(),
                'latex': str(getattr(step, 'latex', '')).strip(),
                'explanation': str(getattr(step, 'explanation', '')).strip()
            }
        
        raise ValueError(f"Cannot serialize step of type {type(step)}: {step}")
    
    @staticmethod
    def serialize_steps(steps: Union[List[Any], Any, None]) -> List[Dict[str, str]]:
        """
        Convert a list of steps to canonical format.
        
        Args:
            steps: Can be:
                - List of Step objects
                - List of dicts
                - Single step
                - None or empty
        
        Returns:
            List of serialized step dicts
        """
        if not steps:
            return []
        
        if isinstance(steps, (str, dict)) or hasattr(steps, '__dataclass_fields__'):
            steps = [steps]
        
        if not isinstance(steps, (list, tuple)):
            return []
        
        serialized = []
        for step in steps:
            try:
                serialized.append(StepSerializer.serialize_step(step))
            except (ValueError, AttributeError, TypeError) as e:
                # Log the error but continue processing other steps
                print(f"Warning: Failed to serialize step: {e}")
                continue
        
        return serialized
    
    @staticmethod
    def validate_step_format(step: Dict[str, str]) -> bool:
        """
        Validate that a step dict has the required format.
        
        Returns:
            True if valid (has title and latex as strings)
        """
        if not isinstance(step, dict):
            return False
        
        return (
            isinstance(step.get('title'), str) and
            isinstance(step.get('latex'), str) and
            isinstance(step.get('explanation'), str)
        )
    
    @staticmethod
    def clean_latex_for_rendering(latex_expr: str) -> str:
        r"""
        Prepare LaTeX for frontend rendering.
        
        Ensures:
        - No embedded $ or $$ delimiters
        - Safe for MathJax wrapping
        
        Args:
            latex_expr: Raw LaTeX expression
        
        Returns:
            Clean LaTeX ready for wrapping with \[...\]
        """
        if not latex_expr:
            return ''
        
        expr = str(latex_expr).strip()
        
        # Remove delimiters that should not be in stored data
        expr = expr.replace('\\[', '').replace('\\]', '')
        expr = expr.replace('$$', '').replace('$', '')
        expr = expr.replace('\\(', '').replace('\\)', '')
        
        return expr.strip()
    
    @staticmethod
    def format_step_for_pdf(step: Dict[str, str], step_number: int) -> Dict[str, Any]:
        """
        Format a serialized step for PDF generation.
        
        Ensures:
        - Proper LaTeX without delimiters
        - All text fields are strings
        - Additional metadata for PDF layout
        
        Args:
            step: Serialized step dict
            step_number: Step index (1-based)
        
        Returns:
            Dict with title, latex, explanation, step_number
        """
        return {
            'step_number': step_number,
            'title': StepSerializer.clean_latex_for_rendering(step.get('title', '')),
            'latex': StepSerializer.clean_latex_for_rendering(step.get('latex', '')),
            'explanation': step.get('explanation', ''),
        }


def serialize_result_with_steps(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a math_engine result to ensure steps are properly serialized.
    
    This function is called by views.py before returning JSON to ensure
    the response contains only serializable primitives.
    
    Args:
        result: Result dict from math_engine with possible step objects
    
    Returns:
        Normalized result dict with steps as list of dicts
    """
    if not isinstance(result, dict):
        return result
    
    # Copy to avoid mutating original
    normalized = dict(result)
    
    # Serialize steps if present
    if 'steps' in normalized:
        normalized['steps'] = StepSerializer.serialize_steps(normalized['steps'])
    
    # Ensure all values are serializable primitives
    for key in ['result', 'latex', 'original_expression']:
        if key in normalized:
            normalized[key] = str(normalized[key]) if normalized[key] is not None else ''
    
    return normalized
