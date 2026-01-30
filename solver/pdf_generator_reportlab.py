"""
Alternative PDF Generator using ReportLab
Generates professional Wolfram-style PDFs with minimal system dependencies
"""

import io
import re
import base64
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, Color
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether, Image
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# Import step serializer for proper step handling
from .step_serializer import StepSerializer
from .graph_generator import GraphGenerator


def clean_latex(expr):
    """Remove LaTeX delimiters to get clean expression"""
    if not expr:
        return expr
    # Remove all LaTeX delimiters
    expr = str(expr).replace('\\[', '').replace('\\]', '')
    expr = expr.replace('$$', '').replace('$', '')
    expr = expr.replace('\\(', '').replace('\\)', '')
    expr = expr.strip()
    return expr


def latex_to_readable(expr):
    """
    Convert LaTeX notation to readable text format for PDF rendering.
    ReportLab doesn't render LaTeX, so we convert to plain text/unicode.
    """
    if not expr:
        return expr
    
    expr = str(expr).strip()
    
    # Remove delimiters first
    expr = clean_latex(expr)
    
    # Handle \left and \right brackets/parens
    expr = expr.replace('\\left(', '(').replace('\\right)', ')')
    expr = expr.replace('\\left[', '[').replace('\\right]', ']')
    expr = expr.replace('\\left{', '{').replace('\\right}', '}')
    expr = expr.replace('\\left|', '|').replace('\\right|', '|')
    
    # Convert common LaTeX patterns to readable text
    # Handle \sqrt with proper bracket matching
    def replace_sqrt(match):
        content = match.group(1).strip()
        # Add parens only if content has operators (spaces between tokens)
        if ' ' in content or any(op in content for op in ['+', '-', '/', '*']):
            return f'√({content})'
        else:
            return f'√{content}'
    expr = re.sub(r'\\sqrt\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', replace_sqrt, expr)
    
    replacements = {
        r'\\frac\{([^}]+)\}\{([^}]+)\}': r'\1/\2',  # \frac{a}{b} -> a/b
        r'\\cdot': '·',  # \cdot -> ·
        r'\\pi': 'π',  # \pi -> π
        r'\\infty': '∞',  # \infty -> ∞
        r'\\alpha': 'α',
        r'\\beta': 'β',
        r'\\gamma': 'γ',
        r'\\delta': 'δ',
        r'\\theta': 'θ',
        r'\\lambda': 'λ',
        r'\\mu': 'μ',
        r'\\nu': 'ν',
        r'\\xi': 'ξ',
        r'\\rho': 'ρ',
        r'\\sigma': 'σ',
        r'\\tau': 'τ',
        r'\\phi': 'φ',
        r'\\psi': 'ψ',
        r'\\omega': 'ω',
        r'\\pm': '±',
        r'\\times': '×',
        r'\\div': '÷',
        r'\\neq': '≠',
        r'\\leq': '≤',
        r'\\geq': '≥',
        r'\\approx': '≈',
        r'\\equiv': '≡',
        r'\\sum': 'Σ',
        r'\\prod': 'Π',
        r'\\int': '∫',
        r'\\partial': '∂',
        r'\\nabla': '∇',
        r'\\forall': '∀',
        r'\\exists': '∃',
        r'\\in': '∈',
        r'\\notin': '∉',
        r'\\subset': '⊂',
        r'\\supset': '⊃',
        r'\\cup': '∪',
        r'\\cap': '∩',
    }
    
    for latex, text in replacements.items():
        expr = re.sub(latex, text, expr)
    
    # Handle superscripts: x^2 -> x²
    expr = re.sub(r'\^(\d)', lambda m: {
        '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵',
        '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '0': '⁰'
    }.get(m.group(1), m.group(0)), expr)
    
    # Handle subscripts: x_i -> xᵢ (basic support)
    expr = re.sub(r'_(\d)', lambda m: {
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'
    }.get(m.group(1), m.group(0)), expr)
    
    # Handle remaining variations
    expr = expr.replace('\\cdot', '·')
    expr = expr.replace('\\times', '×')
    expr = expr.replace('\\div', '÷')
    
    # Clean up any remaining common LaTeX commands that couldn't be regex matched
    expr = expr.replace('\\right', '').replace('\\left', '')
    expr = expr.replace('\\displaystyle', '').replace('\\textstyle', '')
    expr = expr.replace('\\rm', '').replace('\\bf', '').replace('\\it', '')
    expr = expr.replace('\\mathrm', '').replace('\\mathbf', '')
    
    # Clean up remaining backslashes (unmatched LaTeX commands)
    expr = re.sub(r'\\[a-zA-Z]+', '', expr)  # Remove any remaining \command patterns
    expr = expr.replace('\\', '')  # Remove any remaining lone backslashes
    
    # Clean up extra spaces
    expr = re.sub(r'\s+', ' ', expr).strip()

    # Remove all remaining curly braces (flatten nested braces)
    expr = expr.replace('{', '').replace('}', '')

    return expr


def generate_pdf_with_reportlab(calculation_data, user=None):
    """
    Generate a professional PDF using ReportLab
    
    Args:
        calculation_data: dict with operation, expression, result, timestamp
        user: Optional user object for attribution
    
    Returns:
        PDF bytes
    """
    # Create PDF buffer
    pdf_buffer = io.BytesIO()
    
    # Create document
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Style definitions
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#2c3e50'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=HexColor('#666666'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderPadding=5,
        borderColor=HexColor('#dddddd'),
        borderWidth=1,
        borderRadius=3
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor=HexColor('#333333'),
        fontName='Helvetica'
    )
    
    math_style = ParagraphStyle(
        'Math',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        textColor=HexColor('#1a1a1a'),
        fontName='Courier',
        alignment=TA_CENTER,
        spaceAfter=8
    )
    
    # Build document elements
    elements = []
    
    # Header
    operation = calculation_data.get('operation', 'Calculation').title()
    elements.append(Paragraph(f"TfeaterMathLab: {operation}", title_style))
    
    # Timestamp and user
    timestamp = calculation_data.get('timestamp')
    if timestamp:
        if hasattr(timestamp, 'strftime'):
            timestamp_str = timestamp.strftime('%B %d, %Y at %I:%M %p')
        else:
            timestamp_str = str(timestamp)
        
        user_info = f"Generated on {timestamp_str}"
        if user and hasattr(user, 'username'):
            user_info += f" by {user.username}"
        
        elements.append(Paragraph(user_info, subtitle_style))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Input section
    expression = calculation_data.get('expression', '')
    if expression:
        elements.append(Paragraph("Input Expression", heading_style))
        elements.append(Paragraph(f"<b>{latex_to_readable(expression)}</b>", math_style))
        elements.append(Spacer(1, 0.1*inch))
    
    # Steps section
    result_data = calculation_data.get('result', {})
    steps = result_data.get('steps', []) if isinstance(result_data, dict) else []
    if steps:
        elements.append(Paragraph("Solution Steps", heading_style))
        serialized_steps = StepSerializer.serialize_steps(steps)
        step_rows = []
        for i, step in enumerate(serialized_steps, 1):
            try:
                title = step.get('title', f'Step {i}')
                latex = step.get('latex', '')
                explanation = step.get('explanation', '')
                cell_html = f"<b>{latex_to_readable(title)}</b>"
                if latex:
                    readable_latex = latex_to_readable(latex)
                    cell_html += f"<br/><font name='Courier' size='11' color='#1a1a1a'>{readable_latex}</font>"
                if explanation:
                    readable_explanation = latex_to_readable(explanation)
                    cell_html += f"<br/><font size='10' color='#2c3e50'>{readable_explanation}</font>"
                step_rows.append([
                    Paragraph(f"<b>{i}.</b>", normal_style),
                    Paragraph(cell_html, normal_style)
                ])
            except (KeyError, AttributeError, TypeError) as e:
                step_rows.append([
                    Paragraph(f"<b>{i}.</b>", normal_style),
                    Paragraph(latex_to_readable(str(step)), math_style)
                ])
        if step_rows:
            step_table = Table(
                step_rows,
                colWidths=[0.3*inch, 5.2*inch],
                style=TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    # Professional background for both light and dark mode
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [HexColor('#f5f6fa'), HexColor('#e1e6ef')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#b0b0b0')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ])
            )
            elements.append(step_table)
            elements.append(Spacer(1, 0.15*inch))
    
    # Result section
    result_latex = result_data.get('latex', '') if isinstance(result_data, dict) else str(result_data)
    result = result_data.get('result', result_latex) if isinstance(result_data, dict) else result_latex
    
    if result or result_latex:
        elements.append(Paragraph("Result", heading_style))
        result_text = result or result_latex
        readable_result = latex_to_readable(result_text)
        # Professional result box for both light and dark mode
        result_table = Table(
            [[Paragraph(f"<b>{readable_result}</b>", math_style)]],
            colWidths=[5.5*inch],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#e8eaef')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BORDER', (0, 0), (-1, -1), 2, HexColor('#2c3e50')),
                ('LEFTPADDING', (0, 0), (-1, -1), 14),
                ('RIGHTPADDING', (0, 0), (-1, -1), 14),
                ('TOPPADDING', (0, 0), (-1, -1), 16),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
            ])
        )
        elements.append(result_table)
        elements.append(Spacer(1, 0.15*inch))
    
    # Optional graph section: attempt to generate a graph for the main
    # expression when it is graphable. Failures are silently ignored so
    # PDF generation never breaks because of graph issues.
    expression_for_graph = calculation_data.get('expression', '')
    if expression_for_graph:
        try:
            graph_generator = GraphGenerator()
            image_base64 = graph_generator.generate_plot(expression_for_graph)
            image_bytes = base64.b64decode(image_base64)
            image_buffer = io.BytesIO(image_bytes)

            elements.append(Paragraph("Graph", heading_style))
            # Reasonable default size; ReportLab will maintain aspect ratio.
            graph_image = Image(image_buffer, width=5.5*inch, height=3.2*inch)
            elements.append(graph_image)
            elements.append(Spacer(1, 0.15*inch))
        except Exception:
            # If graph generation fails for this expression, skip the section.
            pass
    
    # Advanced properties (for matrix operations)
    properties = [k for k in calculation_data.keys() 
                  if k in ['trace', 'determinant', 'eigenvalues', 'eigenvectors', 
                          'characteristic_polynomial', 'condition_number']]
    
    if properties:
        elements.append(Paragraph("Properties", heading_style))
        
        property_rows = []
        property_map = {
            'trace': 'Trace',
            'determinant': 'Determinant',
            'eigenvalues': 'Eigenvalues',
            'eigenvectors': 'Eigenvectors',
            'characteristic_polynomial': 'Characteristic Polynomial',
            'condition_number': 'Condition Number'
        }
        
        for prop in properties:
            if prop in calculation_data:
                value = calculation_data[prop]
                label = property_map.get(prop, prop.replace('_', ' ').title())
                clean_value = latex_to_readable(str(value))
                property_rows.append([
                    Paragraph(f"<b>{label}:</b>", normal_style),
                    Paragraph(clean_value, math_style)
                ])
        
        if property_rows:
            prop_table = Table(
                property_rows,
                colWidths=[2*inch, 3.5*inch],
                style=TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, HexColor('#f9f9f9')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dddddd')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ])
            )
            elements.append(prop_table)
            elements.append(Spacer(1, 0.15*inch))
    
    # Explanation section
    explanation = result_data.get('detailed_explanation', {}) if isinstance(result_data, dict) else {}
    
    if explanation and isinstance(explanation, dict):
        method = explanation.get('method', '')
        concepts = explanation.get('key_concepts', [])
        tips = explanation.get('tips', [])
        
        if method or concepts or tips:
            elements.append(Paragraph("Explanation", heading_style))
            
            if method:
                elements.append(Paragraph(f"<b>Method:</b> {method}", normal_style))
                elements.append(Spacer(1, 0.08*inch))
            
            if concepts:
                concepts_text = ", ".join(concepts)
                elements.append(Paragraph(f"<b>Key Concepts:</b> {concepts_text}", normal_style))
                elements.append(Spacer(1, 0.08*inch))
            
            if tips:
                tips_text = "<br/>".join([f"• {tip}" for tip in tips])
                elements.append(Paragraph(f"<b>Tips:</b>", normal_style))
                elements.append(Paragraph(tips_text, normal_style))
                elements.append(Spacer(1, 0.1*inch))
    
    # Footer
    elements.append(Spacer(1, 0.2*inch))
    footer_text = "Generated by TfeaterMathLab | Professional Mathematical Solutions"
    elements.append(Paragraph(f"<i>{footer_text}</i>", 
                             ParagraphStyle('Footer', parent=styles['Normal'],
                                          fontSize=9, textColor=HexColor('#999999'),
                                          alignment=TA_CENTER)))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF bytes
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


def generate_pdf_from_calculation_model(calculation):
    """
    Generate PDF from a Calculation model instance
    
    Args:
        calculation: Calculation model instance
    
    Returns:
        PDF bytes
    """
    import json
    
    # Parse result data - try to get from multiple possible fields
    result_data = {}
    
    # Try to parse steps if available
    steps = []
    if hasattr(calculation, 'steps') and calculation.steps:
        if isinstance(calculation.steps, list):
            steps = calculation.steps
        elif isinstance(calculation.steps, str):
            try:
                steps = json.loads(calculation.steps)
            except:
                steps = [calculation.steps]
    
    # Build result data from available fields
    result_latex = getattr(calculation, 'latex_result', '')
    result_value = getattr(calculation, 'result', '')
    
    result_data = {
        'latex': result_latex or result_value,
        'result': result_value,
        'steps': steps
    }
    
    # Build calculation data
    calc_data = {
        'operation': getattr(calculation, 'operation_type', 'calculation'),
        'expression': getattr(calculation, 'parsed_math_expression', ''),
        'result': result_data,
        'timestamp': getattr(calculation, 'created_at', None),
    }
    
    # Add optional advanced properties if they exist
    for prop in ['trace', 'determinant', 'eigenvalues', 'eigenvectors', 
                 'characteristic_polynomial', 'condition_number']:
        if hasattr(calculation, prop):
            calc_data[prop] = getattr(calculation, prop)
    
    # Get user if available
    user = getattr(calculation, 'user', None) if hasattr(calculation, 'user') else None
    
    return generate_pdf_with_reportlab(calc_data, user)


# Backward compatibility function name
def generate_wolfram_style_pdf(calculation_data, user=None):
    """Wrapper for consistency with WeasyPrint version"""
    return generate_pdf_with_reportlab(calculation_data, user)
