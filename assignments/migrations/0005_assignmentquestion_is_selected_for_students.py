                                               

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0004_quiz_timing_and_marks'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignmentquestion',
            name='is_selected_for_students',
            field=models.BooleanField(default=True, help_text='If False, this is a pooled question not shown to students'),
        ),
    ]
