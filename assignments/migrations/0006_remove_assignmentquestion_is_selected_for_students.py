                                               

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0005_assignmentquestion_is_selected_for_students'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assignmentquestion',
            name='is_selected_for_students',
        ),
    ]
