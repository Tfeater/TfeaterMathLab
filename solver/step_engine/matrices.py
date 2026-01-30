"""
Matrix step engine - generates detailed steps for matrix operations.

Supports:
- Determinant calculation (with cofactor expansion)
- Matrix inverse (Gauss-Jordan elimination)
- Matrix transpose
- Row reduction to RREF (Reduced Row Echelon Form)
- Matrix multiplication
"""

from typing import List, Dict, Any, Optional
from .base import Step, StepBuilder
import sympy as sp
from sympy import Matrix, eye, zeros
import re


class MatrixStepBuilder(StepBuilder):
    """Builds step-by-step solutions for matrix operations."""
    
    def build_steps(self, expression: str, context: Dict[str, Any]) -> List[Step]:
        """
        Build steps for a matrix operation.
        
        Args:
            expression: Matrix specification, e.g., "[[1,2],[3,4]]"
            context: Dict with 'operation' (determinant, inverse, transpose, rref)
        
        Returns:
            List of Step objects showing the operation
        """
        try:
            # Parse matrix
            matrix = self._parse_matrix(expression)
            operation = context.get('operation', 'determinant')
            
            steps = []
            
            # Add initial matrix
            steps.append(Step(
                title="Matrix",
                latex=sp.latex(matrix),
                explanation=f"Given matrix for {operation} calculation."
            ))
            
            if operation == 'determinant':
                steps.extend(self._determinant_steps(matrix))
            elif operation == 'inverse':
                steps.extend(self._inverse_steps(matrix))
            elif operation == 'transpose':
                steps.extend(self._transpose_steps(matrix))
            elif operation == 'rref':
                steps.extend(self._rref_steps(matrix))
            elif operation == 'multiply':
                # For multiply, expression should be "[[...],[...]] * [[...],[...]]"
                matrix2 = self._parse_matrix_from_multiply(expression)
                steps.extend(self._multiply_steps(matrix, matrix2))
            else:
                steps.append(Step(
                    title="Unknown operation",
                    latex=operation,
                    explanation=f"Operation '{operation}' not recognized."
                ))
            
            return steps
            
        except Exception as e:
            return [Step(
                title="Error with matrix",
                latex=expression,
                explanation=f"Could not parse or process matrix: {str(e)}"
            )]
    
    def _parse_matrix(self, expression: str) -> Matrix:
        """Parse matrix from string representation like [[1,2],[3,4]]."""
        # Clean up the expression
        expression = expression.strip()
        
        # Try to safely evaluate as nested list using ast.literal_eval
        import ast
        try:
            matrix_list = ast.literal_eval(expression)
            # Convert string entries to SymPy Rational for exact arithmetic
            converted = []
            for row in matrix_list:
                converted_row = []
                for entry in row:
                    try:
                        if isinstance(entry, str):
                            if '/' in entry:
                                converted_row.append(sp.Rational(entry))
                            else:
                                converted_row.append(sp.sympify(entry, rational=True))
                        else:
                            converted_row.append(entry)
                    except (ValueError, SyntaxError):
                        converted_row.append(sp.Symbol(str(entry)))
                converted.append(converted_row)
            return Matrix(converted)
        except (ValueError, SyntaxError):
            # Try parsing comma-separated values by rows (e.g., "1,2;3,4")
            rows = expression.split(';')
            matrix_list = []
            for row in rows:
                row_vals = []
                for val in row.split(','):
                    try:
                        val = val.strip()
                        if '/' in val:
                            row_vals.append(sp.Rational(val))
                        else:
                            row_vals.append(sp.sympify(val, rational=True))
                    except (ValueError, SyntaxError):
                        row_vals.append(sp.Symbol(val))
                matrix_list.append(row_vals)
            return Matrix(matrix_list)
    
    def _parse_matrix_from_multiply(self, expression: str) -> Matrix:
        """Extract second matrix from multiplication expression like 'A * B'."""
        if '*' in expression:
            parts = expression.split('*')
            if len(parts) >= 2:
                return self._parse_matrix(parts[1].strip())
        raise ValueError("Could not extract second matrix")
    
    def _determinant_steps(self, matrix: Matrix) -> List[Step]:
        """Generate steps for calculating determinant."""
        steps = []
        
        m, n = matrix.shape
        if m != n:
            steps.append(Step(
                title="Non-square matrix",
                latex="\\text{Determinant only defined for square matrices}",
                explanation=f"Matrix is {m}×{n}, but determinant requires n×n matrix."
            ))
            return steps
        
        # For 2x2 and 3x3, show manual calculation
        if m == 2:
            a, b = matrix[0, 0], matrix[0, 1]
            c, d = matrix[1, 0], matrix[1, 1]
            
            steps.append(Step(
                title="For 2×2 matrix, use formula",
                latex=f"\\det(A) = {sp.latex(a)}{sp.latex(d)} - {sp.latex(b)}{sp.latex(c)}",
                explanation="For a 2×2 matrix, determinant = ad - bc",
                formula="2×2 determinant: det = ad - bc"
            ))
            
            det = a*d - b*c
            steps.append(Step(
                title="Calculate",
                latex=f"\\det(A) = ({sp.latex(a)})({sp.latex(d)}) - ({sp.latex(b)})({sp.latex(c)}) = {sp.latex(det)}",
                explanation="Multiply diagonals and subtract.",
                operation="calculate"
            ))
        
        elif m == 3:
            steps.append(Step(
                title="Use Rule of Sarrus or cofactor expansion",
                latex="\\det(A) = a_{11}(a_{22}a_{33} - a_{23}a_{32}) - a_{12}(a_{21}a_{33} - a_{23}a_{31}) + a_{13}(a_{21}a_{32} - a_{22}a_{31})",
                explanation="For 3×3 matrix, expand along first row using minors and cofactors.",
                formula="3×3 determinant using cofactor expansion"
            ))
        
        # Final determinant
        det = matrix.det()
        steps.append(Step(
            title="Final answer",
            latex=f"\\det(A) = {sp.latex(det)}",
            explanation=f"The determinant of the matrix is {sp.latex(det)}.",
            operation="solution"
        ))
        
        return steps
    
    def _inverse_steps(self, matrix: Matrix) -> List[Step]:
        """Generate steps for finding matrix inverse using Gauss-Jordan elimination."""
        steps = []
        
        m, n = matrix.shape
        if m != n:
            steps.append(Step(
                title="Non-square matrix",
                latex="\\text{Inverse only defined for square matrices}",
                explanation=f"Matrix is {m}×{n}, inverse only exists for n×n matrices."
            ))
            return steps
        
        # Check if determinant is zero
        det = matrix.det()
        if det == 0:
            steps.append(Step(
                title="Singular matrix",
                latex="\\det(A) = 0",
                explanation="The determinant is 0, so this matrix has no inverse (it's singular)."
            ))
            return steps
        
        # Create augmented matrix [A | I]
        augmented = matrix.row_join(eye(n))
        
        steps.append(Step(
            title="Create augmented matrix [A | I]",
            latex=sp.latex(augmented),
            explanation="Create an augmented matrix with the original matrix on the left and identity matrix on the right.",
            operation="setup"
        ))
        
        # Perform row reduction
        rref_matrix, pivot_cols = augmented.rref()
        
        steps.append(Step(
            title="Row reduce to [I | A⁻¹]",
            latex=sp.latex(rref_matrix),
            explanation="Use row operations to transform the left side into the identity matrix. The right side becomes A⁻¹.",
            formula="Gauss-Jordan elimination",
            operation="row_reduce"
        ))
        
        # Extract inverse
        inverse = rref_matrix[:, n:]
        
        steps.append(Step(
            title="Extract inverse",
            latex=f"A^{{-1}} = {sp.latex(inverse)}",
            explanation="The right side of the reduced augmented matrix is the inverse.",
            operation="solution"
        ))
        
        return steps
    
    def _transpose_steps(self, matrix: Matrix) -> List[Step]:
        """Generate steps for finding matrix transpose."""
        steps = []
        
        m, n = matrix.shape
        
        steps.append(Step(
            title="Swap rows and columns",
            latex="A^T = A^T",
            explanation=f"The transpose swaps rows and columns. Row i becomes column i.",
            formula="Transpose: (A^T)[i,j] = A[j,i]"
        ))
        
        transpose = matrix.T
        
        steps.append(Step(
            title="Result",
            latex=f"A^{{T}} = {sp.latex(transpose)}",
            explanation=f"The transpose of the {m}×{n} matrix is a {n}×{m} matrix.",
            operation="solution"
        ))
        
        return steps
    
    def _rref_steps(self, matrix: Matrix) -> List[Step]:
        """Generate steps for row reduction to RREF."""
        steps = []
        
        steps.append(Step(
            title="Row reduce to RREF",
            latex="\\text{Reduce using Gauss-Jordan elimination}",
            explanation="Use row operations to get the matrix in Reduced Row Echelon Form.",
            formula="RREF: Leading 1's with zeros above and below"
        ))
        
        rref_matrix, pivot_cols = matrix.rref()
        
        steps.append(Step(
            title="RREF form",
            latex=sp.latex(rref_matrix),
            explanation="Each row's leading entry (leftmost non-zero) is 1, and all entries above and below are 0.",
            operation="solution"
        ))
        
        return steps
    
    def _multiply_steps(self, matrix1: Matrix, matrix2: Matrix) -> List[Step]:
        """Generate steps for matrix multiplication."""
        steps = []
        
        m1, n1 = matrix1.shape
        m2, n2 = matrix2.shape
        
        if n1 != m2:
            steps.append(Step(
                title="Incompatible dimensions",
                latex=f"A: {m1} \\times {n1}, \\quad B: {m2} \\times {n2}",
                explanation=f"Matrix multiplication requires columns of A ({n1}) to equal rows of B ({m2}).",
                formula="Requirement: A[m×n] × B[n×p] = C[m×p]"
            ))
            return steps
        
        steps.append(Step(
            title="Matrix multiplication setup",
            latex=f"A[{m1}\\times {n1}] \\times B[{m2}\\times {n2}] = C[{m1}\\times {n2}]",
            explanation=f"The result will be a {m1}×{n2} matrix.",
            formula="Result dimensions: [m×n][n×p] = [m×p]"
        ))
        
        steps.append(Step(
            title="Compute dot products",
            latex="C[i,j] = \\sum_{k=1}^{n} A[i,k] \\cdot B[k,j]",
            explanation="Each element C[i,j] is the dot product of row i of A with column j of B.",
            operation="define"
        ))
        
        result = matrix1 * matrix2
        
        steps.append(Step(
            title="Result",
            latex=sp.latex(result),
            explanation="The product of the two matrices.",
            operation="solution"
        ))
        
        return steps
