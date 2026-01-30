"""
Natural language math parser
"""
import re
from typing import Dict, Any


class NaturalLanguageParser:
    """Parse natural language math problems into structured format"""
    
    def __init__(self):
        self.operations = {
            'derivative': ['derivative', 'derive', 'differentiate', 'diff'],
            'integral': ['integral', 'integrate', 'antiderivative'],
            'solve': ['solve', 'solution', 'root', 'zero'],
            'limit': ['limit', 'approach'],
            'simplify': ['simplify', 'simplification'],
            'factor': ['factor', 'factorize'],
            'expand': ['expand', 'expansion'],
        }
        
        self.variables = ['x', 'y', 'z', 't']
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse natural language text into math operation"""
        text = text.lower().strip()
        
        # Detect operation
        operation = self._detect_operation(text)
        if not operation:
            return {'error': 'Could not detect math operation. Try using words like "solve", "derivative", "integral", etc.'}
        
        # Extract expression
        expression = self._extract_expression(text, operation)
        if not expression:
            return {'error': 'Could not extract mathematical expression from text.'}
        
        # Extract variable if needed
        variable = self._extract_variable(text, operation)
        
        return {
            'operation': operation,
            'expression': expression,
            'variable': variable,
            'parsed_text': f"Operation: {operation}, Expression: {expression}" + (f", Variable: {variable}" if variable else "")
        }
    
    def _detect_operation(self, text: str) -> str:
        """Detect the math operation from text"""
        for op, keywords in self.operations.items():
            for keyword in keywords:
                if keyword in text:
                    return op
        return None
    
    def _extract_expression(self, text: str, operation: str) -> str:
        """Extract the mathematical expression from text"""
        # Remove operation keywords
        for op, keywords in self.operations.items():
            for keyword in keywords:
                text = text.replace(keyword, '')
        
        # Remove common words
        remove_words = ['of', 'for', 'the', 'find', 'calculate', 'compute', 'what', 'is', 'to', 'with', 'respect', 'by']
        for word in remove_words:
            text = re.sub(r'\b' + word + r'\b', '', text)
        
        # Clean up extra spaces and punctuation
        text = re.sub(r'[^\w\s\+\-\*\/\^\(\)\[\]\{\}\=\.\,]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Try to identify the core expression
        # Look for patterns like "x squared", "x^2", "e^x", etc.
        text = self._convert_words_to_math(text)
        
        return text
    
    def _convert_words_to_math(self, text: str) -> str:
        """Convert word descriptions to math notation"""
        # Handle powers
        text = re.sub(r'(\w+)\s+squared', r'\1^2', text)
        text = re.sub(r'(\w+)\s+cubed', r'\1^3', text)
        text = re.sub(r'(\w+)\s+to\s+the\s+power\s+(\w+)', r'\1^\2', text)
        
        # Handle functions
        text = re.sub(r'e\s+to\s+the\s+(\w+)', r'e^\1', text)
        text = re.sub(r'e\s+raised\s+to\s+(\w+)', r'e^\1', text)
        
        # Handle pi and e
        text = text.replace('pi', 'π')
        text = text.replace('euler', 'e')
        
        return text
    
    def _extract_variable(self, text: str, operation: str) -> str:
        """Extract variable for operations that need it"""
        if operation in ['derivative', 'integral', 'limit']:
            # Look for variable mentions
            for var in self.variables:
                if var in text:
                    return var
            # Default to x
            return 'x'
        return None