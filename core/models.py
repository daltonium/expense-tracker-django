from django.db import models
from django.contrib.auth.models import User

class Workspace(models.Model):
    MODE_CHOICES = [
        ('personal', 'Personal / Family'),
        ('company', 'Company'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.mode})"