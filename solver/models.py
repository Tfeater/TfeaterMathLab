from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile for subscriptions and preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription_tier = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('premium', 'Premium'),
        ],
        default='free'
    )
    theme_preference = models.CharField(
        max_length=10,
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
        ],
        default='light'
    )
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username} - {self.subscription_tier}"


class Calculation(models.Model):
    """Store calculation history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    original_input = models.TextField(blank=True)  # Raw user input (for natural language)
    parsed_math_expression = models.TextField()  # Parsed expression
    result = models.TextField()
    latex_result = models.TextField(blank=True, default='')
    operation_type = models.CharField(max_length=50)  # derivative, integral, solve, etc.
    steps = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['operation_type']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', 'operation_type']),
        ]
    
    def __str__(self):
        return f"{self.operation_type}: {self.parsed_math_expression[:50]}"


class Graph(models.Model):
    """Store graph data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    expression = models.TextField(max_length=1000)
    graph_image = models.ImageField(upload_to='graphs/', null=True, blank=True)
    x_min = models.FloatField(default=-10.0)
    x_max = models.FloatField(default=10.0)
    y_min = models.FloatField(null=True, blank=True)
    y_max = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Graph: {self.expression[:50]}"
