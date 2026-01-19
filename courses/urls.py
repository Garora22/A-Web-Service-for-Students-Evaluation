from django.urls import path

from .views import (
    my_courses,
    enter_course,
    professor_course_home,
    ta_course_home,
    student_course_home,
    my_account,
    contact_us,
)

urlpatterns = [
    path('', my_courses, name='my_courses'),
    path('<int:course_id>/enter/', enter_course, name='enter_course'),

    path('<int:course_id>/professor/home/', professor_course_home),
    path('<int:course_id>/ta/home/', ta_course_home),
    path('<int:course_id>/student/home/', student_course_home),
    path("account/", my_account),
    path("contact/", contact_us),
]
