from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class Semester(models.Model):
    year_start = models.IntegerField()   # 2025
    year_end = models.IntegerField()     # 2026
    sem = models.IntegerField(
        choices=[(1, "SEM 1"), (2, "SEM 2"), (3, "SEM 3 : Summer")]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-year_start", "-sem"]
        unique_together = ("year_start", "year_end", "sem")

    def __str__(self):
        return f"{self.year_start}-{self.year_end} SEM {self.sem}"

class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="courses"
    )


    def __str__(self):
        return f"{self.code} - {self.name}"

class CourseProfessor(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE)
    professor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'professor'}
    )

    def __str__(self):
        return f"{self.professor} → {self.course}"

class CourseTA(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    ta = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'ta'}
    )

    class Meta:
        unique_together = ('course', 'ta')

    def __str__(self):
        return f"{self.ta} → {self.course}"

class CourseStudent(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'}
    )

    class Meta:
        unique_together = ('course', 'student')

    def __str__(self):
        return f"{self.student} → {self.course}"
