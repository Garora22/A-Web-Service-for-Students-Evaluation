from django.contrib import admin
from .models import Course, CourseProfessor, CourseTA, CourseStudent, Semester

admin.site.register(Semester)
admin.site.register(Course)
admin.site.register(CourseProfessor)
admin.site.register(CourseTA)
admin.site.register(CourseStudent)