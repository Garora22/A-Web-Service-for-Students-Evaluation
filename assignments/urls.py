from django.urls import path

from .views import (
    assignment_questions,
    assignment_results,
    course_assignments,
    create_assignment,
    delete_assignment,
    edit_assignment,
    generate_mcqs,
    professor_assignments,
    student_assignments,
    student_take_assignment,
)

urlpatterns = [
    path("<int:course_id>/", course_assignments, name="course_assignments"),
    path("<int:course_id>/student/", student_assignments, name="student_assignments"),
    path("<int:course_id>/professor/", professor_assignments, name="professor_assignments"),
    path("<int:course_id>/professor/create/", create_assignment, name="create_assignment"),
    path("<int:course_id>/professor/<int:assignment_id>/edit/", edit_assignment, name="edit_assignment"),
    path("<int:course_id>/professor/<int:assignment_id>/delete/", delete_assignment, name="delete_assignment"),
    path(
        "<int:course_id>/professor/<int:assignment_id>/generate/",
        generate_mcqs,
        name="generate_mcqs",
    ),
    path(
        "<int:course_id>/professor/<int:assignment_id>/questions/",
        assignment_questions,
        name="assignment_questions",
    ),
    path(
        "<int:course_id>/professor/<int:assignment_id>/results/",
        assignment_results,
        name="assignment_results",
    ),
    path(
        "<int:course_id>/student/<int:assignment_id>/take/",
        student_take_assignment,
        name="student_take_assignment",
    ),
]

