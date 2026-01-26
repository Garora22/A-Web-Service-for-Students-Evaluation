from collections import OrderedDict, defaultdict
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import Course, CourseProfessor, CourseTA, CourseStudent, Semester
from content.models import CourseMaterial


@login_required
def my_account(request):
    return render(request, "account/my_account.html", {"nav_active": "account"})

@login_required
def contact_us(request):
    return render(request, "account/contact.html", {"nav_active": "contact"})
@login_required
def my_courses(request):
    user = request.user
    role = user.role

    # 1️⃣ Get ALL enrolled courses
    if role == "student":
        enrollments = (
            CourseStudent.objects
            .filter(student=user)
            .select_related("course__semester")
        )
        courses = [e.course for e in enrollments]

    elif role == "professor":
        enrollments = (
            CourseProfessor.objects
            .filter(professor=user)
            .select_related("course__semester")
        )
        courses = [e.course for e in enrollments]

    elif role == "ta":
        enrollments = (
            CourseTA.objects
            .filter(ta=user)
            .select_related("course__semester")
        )
        courses = [e.course for e in enrollments]

    else:
        courses = []

    # 2️⃣ Get latest 5 semesters globally (THIS WAS MISSING)
    recent_semester_objs = list(
        Semester.objects.order_by("-year_start", "-sem")[:5]
    )

    recent_semesters = OrderedDict((sem, []) for sem in recent_semester_objs)
    previous_semesters = defaultdict(list)

    # 3️⃣ Attach courses to correct bucket
    for course in courses:
        sem = course.semester

        if sem in recent_semesters:
            recent_semesters[sem].append(course)
        else:
            previous_semesters[sem].append(course)

    return render(
        request,
        "courses/my_courses.html",
        {
            "recent_semesters": recent_semesters,
            "previous_semesters": dict(previous_semesters),
            "nav_active": "courses",
        }
    )

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

    course = Course.objects.select_related('semester').get(id=course_id)
    materials = CourseMaterial.objects.filter(course_id=course_id)
    
    # Calculate stats
    total_materials = materials.count()
    published_count = materials.filter(is_published=True).count()
    unpublished_count = total_materials - published_count

    return render(request, 'courses/professor_home.html', {
        'course': course,
        'materials': materials,
        'content_types': CourseMaterial.CONTENT_TYPE_CHOICES,
        'course_id': course_id,
        'total_materials': total_materials,
        'published_count': published_count,
        'unpublished_count': unpublished_count,
    })



@login_required
def ta_course_home(request, course_id):
    if not CourseTA.objects.filter(course_id=course_id, ta=request.user).exists():
        return redirect('/courses/')

    course = Course.objects.select_related('semester').get(id=course_id)
    materials = CourseMaterial.objects.filter(course_id=course_id, is_published=True)

    return render(request, 'courses/ta_home.html', {
        'course': course,
        'materials': materials,
        'course_id': course_id
    })


@login_required
def student_course_home(request, course_id):
    if not CourseStudent.objects.filter(course_id=course_id, student=request.user).exists():
        return redirect('/courses/')

    course = Course.objects.select_related('semester').get(id=course_id)
    materials = CourseMaterial.objects.filter(course_id=course_id, is_published=True)

    return render(request, 'courses/student_home.html', {
        'course': course,
        'materials': materials,
        'course_id': course_id
    })

