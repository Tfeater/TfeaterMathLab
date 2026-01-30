"""
PDF Export Views for Math Solver
"""
import logging
import json
from datetime import datetime
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone

from .pdf_generator_reportlab import generate_pdf_from_calculation_model
from .models import Calculation

logger = logging.getLogger(__name__)


class ExportPDFView(View):
    """View for exporting a single calculation as PDF."""
    
    def get_calculation(self, calc_id, user):
        """Retrieve calculation with proper access control."""
        try:
            if user.is_authenticated:
                return Calculation.objects.get(id=calc_id, user=user)
            else:
                return Calculation.objects.get(id=calc_id, user__isnull=True)
        except Calculation.DoesNotExist:
            raise Http404("Calculation not found")
    
    @method_decorator(require_http_methods(["GET"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, calc_id):
        """Export calculation as PDF."""
        try:
            calculation = self.get_calculation(calc_id, request.user)
            pdf_bytes = generate_pdf_from_calculation_model(calculation)
            
            filename = f"solution_{calculation.operation_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(pdf_bytes)
            
            return response
        except Http404:
            return HttpResponse("Calculation not found", status=404)
        except ImportError as e:
            logger.error(f"PDF generation dependency missing: {e}")
            return HttpResponse("WeasyPrint is required for PDF export. Please install it.", status=500)
        except Exception as e:
            logger.error(f"PDF export error: {e}")
            return HttpResponse(f"Error generating PDF: {str(e)}", status=500)


class ExportCurrentPDFView(View):
    """View for exporting the most recent calculation as PDF."""
    
    @method_decorator(require_http_methods(["GET"]))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        """Export most recent calculation as PDF."""
        try:
            if request.user.is_authenticated:
                calculation = Calculation.objects.filter(
                    user=request.user
                ).order_by('-created_at').first()
            else:
                calculation = Calculation.objects.filter(
                    user__isnull=True
                ).order_by('-created_at').first()
            
            if not calculation:
                return HttpResponse("No calculations found", status=404)
            
            pdf_bytes = generate_pdf_from_calculation_model(calculation)
            
            filename = f"solution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(pdf_bytes)
            
            return response
        except ImportError as e:
            logger.error(f"PDF generation dependency missing: {e}")
            return HttpResponse("WeasyPrint is required for PDF export. Please install it.", status=500)
        except Exception as e:
            logger.error(f"PDF export error: {e}")
            return HttpResponse(f"Error generating PDF: {str(e)}", status=500)


@login_required
@require_http_methods(["GET"])
def export_history_pdf(request):
    """Export multiple calculations from history as PDF."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.colors import HexColor
        
        calc_ids = request.GET.get('ids', '').split(',')
        calc_ids = [int(i.strip()) for i in calc_ids if i.strip()]
        
        if not calc_ids:
            calculations = Calculation.objects.filter(
                user=request.user
            ).order_by('-created_at')[:10]
        else:
            calculations = Calculation.objects.filter(
                id__in=calc_ids,
                user=request.user
            ).order_by('-created_at')
        
        if not calculations:
            return HttpResponse("No calculations found", status=404)
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,
            textColor=HexColor('#2c3e50')
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=20,
            alignment=1,
            textColor=HexColor('#666666')
        )
        
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=HexColor('#2c3e50'),
            backColor=HexColor('#e8f4fc'),
            leftPadding=12,
            topPadding=8,
            bottomPadding=8
        )
        
        normal_style = styles['Normal']
        
        problem_box_style = ParagraphStyle(
            'ProblemBox',
            parent=styles['Normal'],
            fontSize=16,
            spaceBefore=10,
            spaceAfter=20,
            textColor=HexColor('#1a1a1a'),
            backColor=HexColor('#fff3cd'),
            borderPadding=20,
            borderWidth=1,
            borderColor=HexColor('#ffc107')
        )
        
        result_box_style = ParagraphStyle(
            'ResultBox',
            parent=styles['Normal'],
            fontSize=22,
            spaceBefore=15,
            spaceAfter=15,
            textColor=HexColor('#1a1a1a'),
            backColor=HexColor('#d4edda'),
            borderPadding=25,
            borderWidth=2,
            borderColor=HexColor('#28a745'),
            alignment=1
        )
        
        story = []
        
        story.append(Paragraph('MathSolver', title_style))
        story.append(Paragraph('Solution History', subtitle_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"User: {request.user.username}", normal_style))
        story.append(Paragraph(f"Generated: {timezone.now().strftime('%B %d, %Y at %H:%M')}", normal_style))
        story.append(Spacer(1, 20))
        
        for calc in calculations:
            story.append(Paragraph(f"Operation: {calc.operation_type.title()}", section_title_style))
            
            problem_input = calc.original_input or calc.parsed_math_expression
            story.append(Paragraph(f"Expression: {problem_input}", problem_box_style))
            
            result_text = calc.result
            story.append(Paragraph(f"Result: {result_text}", result_box_style))
            story.append(Spacer(1, 15))
            
            steps = calc.steps or []
            if steps:
                story.append(Paragraph("Steps:", normal_style))
                for i, step in enumerate(steps[:5], 1):
                    story.append(Paragraph(f"  {i}. {step}", normal_style))
            
            story.append(PageBreak())
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        filename = f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"History PDF export error: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)
