from django.conf import settings
from django.db import models

from courses.models import Course

User = settings.AUTH_USER_MODEL


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_assignments")

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=20)

    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-due_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.course.code}: {self.title}"


class AssignmentQuestion(models.Model):
    OPTION_CHOICES = [
        ("A", "Option A"),
        ("B", "Option B"),
        ("C", "Option C"),
        ("D", "Option D"),
    ]

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    difficulty = models.CharField(
        max_length=10,
        choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
        default="easy",
    )
    marks = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Q for {self.assignment_id}: {self.question_text[:50]}"


class StudentAnswer(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        AssignmentQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assignment_answers",
    )
    selected_option = models.CharField(
        max_length=1,
        choices=AssignmentQuestion.OPTION_CHOICES,
    )
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("assignment", "question", "student")

    def __str__(self) -> str:
        return f"Answer by {self.student_id} for Q{self.question_id}"


class StudentAttempt(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assignment_attempts",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    submitted_at = models.DateTimeField(blank=True, null=True)
    seed = models.CharField(max_length=64)
    score = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("assignment", "student")

    def __str__(self) -> str:
        return f"Attempt {self.assignment_id} by {self.student_id}"

