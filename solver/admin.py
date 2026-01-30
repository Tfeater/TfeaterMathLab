from django.contrib import admin
from .models import Calculation, Graph, UserProfile


@admin.register(Calculation)
class CalculationAdmin(admin.ModelAdmin):
    list_display = ['parsed_math_expression', 'operation_type', 'created_at', 'user']
    list_filter = ['operation_type', 'created_at', 'user']
    search_fields = ['parsed_math_expression', 'result', 'original_input']


@admin.register(Graph)
class GraphAdmin(admin.ModelAdmin):
    list_display = ['expression', 'x_min', 'x_max', 'y_min', 'y_max', 'created_at', 'user']
    list_filter = ['created_at', 'user']
    search_fields = ['expression']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_tier', 'theme_preference', 'created_at']
    list_filter = ['subscription_tier', 'theme_preference', 'created_at']
    search_fields = ['user__username', 'user__email']
