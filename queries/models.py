from django.db import models
from django.conf import settings
from courses.models import Course

User = settings.AUTH_USER_MODEL


class Query(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='queries')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_queries')
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = 'Queries'

    def __str__(self):
        return f"{self.title} - {self.student.username}"


class QueryMessage(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    attachment = models.FileField(upload_to='query_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}"
