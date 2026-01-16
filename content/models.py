from django.db import models
from courses.models import Course

class CourseMaterial(models.Model):

    CONTENT_TYPE_CHOICES = [
        ('notes', 'Lecture Notes'),
        ('slides', 'Slides'),
        ('ppt', 'PPT'),
        ('pyq', 'Previous Year Questions'),
        ('other', 'Other'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES
    )
    file = models.FileField(upload_to='course_materials/')
    is_published = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.code} - {self.title}"
