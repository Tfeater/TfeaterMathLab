from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views
from . import pdf_export

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('documentation/', views.documentation, name='documentation'),
    path('history/', login_required(views.history), name='history'),
    path('profile/', login_required(views.profile), name='profile'),
    path('api/solve/', views.solve, name='solve'),
    path('api/solve/text/', views.solve_text_with_cerebras, name='solve_text_with_cerebras'),
    path('api/graph/', views.generate_graph, name='generate_graph'),
    path('api/history/', views.get_history, name='get_history'),
    path('api/parse-natural/', views.parse_natural_language, name='parse_natural'),
    path('register/', views.register, name='register'),
    path('delete-calculation/<int:calc_id>/', views.delete_calculation, name='delete_calculation'),
    
    # PDF Export URLs
    path('api/export/pdf/<int:calc_id>/', pdf_export.ExportPDFView.as_view(), name='export_pdf'),
    path('api/export/pdf/current/', pdf_export.ExportCurrentPDFView.as_view(), name='export_pdf_current'),
    path('api/export/history/pdf/', login_required(pdf_export.export_history_pdf), name='export_history_pdf'),
]
