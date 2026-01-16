from collections import defaultdict
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import CourseProfessor, CourseTA, CourseStudent
from content.models import CourseMaterial

def my_courses(request):
    user = request.user
    role = user.role

    semester_map = defaultdict(list)

    if role == "student":
        enrollments = CourseStudent.objects.filter(student=user).select_related("course__semester")
        for e in enrollments:
            semester_map[e.course.semester].append(e.course)

    elif role == "professor":
        enrollments = CourseProfessor.objects.filter(professor=user).select_related("course__semester")
        for e in enrollments:
            semester_map[e.course.semester].append(e.course)

    elif role == "ta":
        enrollments = CourseTA.objects.filter(ta=user).select_related("course__semester")
        for e in enrollments:
            semester_map[e.course.semester].append(e.course)

    # split active / inactive semesters
    active = {s: c for s, c in semester_map.items() if s.is_active}
    inactive = {s: c for s, c in semester_map.items() if not s.is_active}

    return render(request, "courses/my_courses.html", {
        "active_semesters": active,
        "inactive_semesters": inactive
    })



@login_required
def enter_course(request, course_id):
    user = request.user

    if CourseProfessor.objects.filter(course_id=course_id, professor=user).exists():
        return redirect(f'/courses/{course_id}/professor/home/')

    if CourseTA.objects.filter(course_id=course_id, ta=user).exists():
        return redirect(f'/courses/{course_id}/ta/home/')

    if CourseStudent.objects.filter(course_id=course_id, student=user).exists():
        return redirect(f'/courses/{course_id}/student/home/')

    # Not authorized
    return redirect('/courses/')

@login_required
def professor_course_home(request, course_id):
    if not CourseProfessor.objects.filter(course_id=course_id, professor=request.user).exists():
        return redirect('/courses/')

    if request.method == 'POST':
        CourseMaterial.objects.create(
            course_id=course_id,
            title=request.POST['title'],
            content_type=request.POST['content_type'],
            file=request.FILES['file'],
            is_published=('is_published' in request.POST)
        )
        return redirect(request.path)

    materials = CourseMaterial.objects.filter(course_id=course_id)

    return render(request, 'courses/professor_home.html', {
        'materials': materials,
        'content_types': CourseMaterial.CONTENT_TYPE_CHOICES,
        'course_id': course_id
    })



@login_required
def ta_course_home(request, course_id):
    if not CourseTA.objects.filter(course_id=course_id, ta=request.user).exists():
        return redirect('/courses/')

    materials = CourseMaterial.objects.filter(course_id=course_id)

    return render(request, 'courses/ta_home.html', {
        'materials': materials
    })


@login_required
def student_course_home(request, course_id):
    if not CourseStudent.objects.filter(course_id=course_id, student=request.user).exists():
        return redirect('/courses/')

    materials = CourseMaterial.objects.filter(course_id=course_id, is_published=True)

    return render(request, 'courses/student_home.html', {
        'materials': materials
    })

