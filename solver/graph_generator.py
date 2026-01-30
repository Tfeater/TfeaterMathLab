"""
Graph generator using Matplotlib
"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp
from io import BytesIO
from typing import Tuple, Optional
import base64


class GraphGenerator:
    """Generate graphs for mathematical expressions"""
    
    def __init__(self):
        self.x, self.y, self.z = sp.symbols('x y z')
    
    def generate_plot(self, expression: str, x_range: Tuple[float, float] = (-10, 10),
                     y_range: Optional[Tuple[float, float]] = None, num_points: int = 1000) -> str:
        """Generate a plot and return as base64 encoded image"""
        # Parse expression safely with sympy. Any parsing or evaluation
        # error should be propagated to the caller so it can decide how
        # to handle fallbacks. We explicitly avoid drawing an "error"
        # graph with Matplotlib text, to keep the UI clean.
        expr_str = expression.replace('^', '**')

        # Create safe symbol mapping
        safe_dict = {
            'x': self.x, 'y': self.y, 'z': self.z,
            'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
            'cot': sp.cot, 'sec': sp.sec, 'csc': sp.csc,
            'log': sp.log, 'ln': sp.log, 'sqrt': sp.sqrt,
            'exp': sp.exp, 'Abs': sp.Abs, 'oo': sp.oo,
            'e': sp.E, 'pi': sp.pi,
            '__builtins__': {}
        }

        # Use sympify instead of eval for security
        expr = sp.sympify(expr_str, locals=safe_dict)

        # Convert to numerical function
        f = sp.lambdify(self.x, expr, modules=['numpy'])

        # Generate x values
        x_vals = np.linspace(x_range[0], x_range[1], num_points)

        # Calculate y values
        try:
            y_vals = f(x_vals)
            # Handle complex numbers
            y_vals = np.real(y_vals)
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression for graph: {e}") from e

        # Create plot with grayscale theme
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
        ax.plot(x_vals, y_vals, color='#2c2c2c', linewidth=2)
        ax.set_xlabel('x', color='#1a1a1a', fontsize=12)
        ax.set_ylabel('y', color='#1a1a1a', fontsize=12)
        ax.set_title(f'f(x) = {str(expression)}', color='#1a1a1a', fontsize=14)
        ax.grid(True, color='#cccccc', linestyle='--', alpha=0.5)
        ax.set_facecolor('#f9f9f9')
        ax.spines['top'].set_color('#888888')
        ax.spines['right'].set_color('#888888')
        ax.spines['bottom'].set_color('#888888')
        ax.spines['left'].set_color('#888888')

        if y_range:
            ax.set_ylim(y_range)

        plt.tight_layout()

        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return image_base64
    
    def generate_3d_plot(self, expression: str, x_range: Tuple[float, float] = (-5, 5),
                        y_range: Tuple[float, float] = (-5, 5)) -> str:
        """Generate 3D plot"""
        try:
            from mpl_toolkits.mplot3d import Axes3D
            
            # Parse expression safely with sympy
            expr_str = expression.replace('^', '**')
            
            # Create safe symbol mapping
            safe_dict = {
                'x': self.x, 'y': self.y, 'z': self.z,
                'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
                'cot': sp.cot, 'sec': sp.sec, 'csc': sp.csc,
                'log': sp.log, 'ln': sp.log, 'sqrt': sp.sqrt,
                'exp': sp.exp, 'Abs': sp.Abs, 'oo': sp.oo,
                'e': sp.E, 'pi': sp.pi,
                '__builtins__': {}
            }
            
            # Use sympify instead of eval for security
            expr = sp.sympify(expr_str, locals=safe_dict)
            
            # Convert to numerical function
            f = sp.lambdify((self.x, self.y), expr, modules=['numpy'])
            
            # Generate grid
            x_vals = np.linspace(x_range[0], x_range[1], 50)
            y_vals = np.linspace(y_range[0], y_range[1], 50)
            X, Y = np.meshgrid(x_vals, y_vals)
            Z = f(X, Y)
            
            # Create 3D plot
            fig = plt.figure(figsize=(10, 8), facecolor='white')
            ax = fig.add_subplot(111, projection='3d')
            ax.plot_surface(X, Y, Z, cmap='gray', alpha=0.8)
            ax.set_xlabel('x', color='#1a1a1a')
            ax.set_ylabel('y', color='#1a1a1a')
            ax.set_zlabel('z', color='#1a1a1a')
            ax.set_title(f'f(x,y) = {str(expression)}', color='#1a1a1a')
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            return image_base64
        except Exception as e:
            return f"Error generating 3D plot: {str(e)}"
