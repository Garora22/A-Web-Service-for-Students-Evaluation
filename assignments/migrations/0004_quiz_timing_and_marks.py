                                               

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("assignments", "0003_studentanswer"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="assignment",
            name="duration_minutes",
            field=models.PositiveIntegerField(default=20),
        ),
        migrations.AddField(
            model_name="assignmentquestion",
            name="difficulty",
            field=models.CharField(
                choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
                default="easy",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="assignmentquestion",
            name="marks",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.CreateModel(
            name="StudentAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("seed", models.CharField(max_length=64)),
                ("score", models.PositiveIntegerField(default=0)),
                ("total_marks", models.PositiveIntegerField(default=0)),
                (
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attempts",
                        to="assignments.assignment",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignment_attempts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("assignment", "student")},
            },
        ),
    ]

