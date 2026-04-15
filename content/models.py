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


class CourseMaterialText(models.Model):
    """
    Cached extracted text for a CourseMaterial file.
    This lets us avoid re-parsing PDFs/PPTX each time we generate MCQs.
    """

    material = models.OneToOneField(
        CourseMaterial,
        on_delete=models.CASCADE,
        related_name="extracted_text",
    )
    file_name = models.CharField(max_length=500, blank=True)
    kind = models.CharField(max_length=20, blank=True)  # pdf/pptx/text
    text = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("ok", "OK"),
            ("unsupported", "Unsupported"),
            ("error", "Error"),
        ],
        default="ok",
    )
    error_message = models.TextField(blank=True)
    extracted_at = models.DateTimeField(auto_now=True)
    extractor_version = models.CharField(max_length=50, default="v1")
