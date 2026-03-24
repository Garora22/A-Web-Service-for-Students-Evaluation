from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from courses.models import Course, CourseProfessor, CourseStudent, CourseTA

from .models import Assignment, AssignmentQuestion, StudentAnswer
from .services import generate_mcqs_for_assignment


@login_required
def course_assignments(request, course_id: int):
    """
    Single entrypoint used by the "Assignments" button.
    Redirects to the correct page based on course membership/role.
    """
    user = request.user

    if CourseProfessor.objects.filter(course_id=course_id, professor=user).exists():
        return redirect(f"/assignments/{course_id}/professor/")

    if CourseTA.objects.filter(course_id=course_id, ta=user).exists():
        return redirect(f"/assignments/{course_id}/student/")

    if CourseStudent.objects.filter(course_id=course_id, student=user).exists():
        return redirect(f"/assignments/{course_id}/student/")

    return redirect("/courses/")


@login_required
def student_assignments(request, course_id: int):
    if not (
        CourseStudent.objects.filter(course_id=course_id, student=request.user).exists()
        or CourseTA.objects.filter(course_id=course_id, ta=request.user).exists()
    ):
        return redirect("/courses/")

    course = Course.objects.select_related("semester").get(id=course_id)
    now = timezone.now()

    qs = (
        Assignment.objects.filter(course_id=course_id, is_published=True)
        .annotate(
            total_answers=Count(
                "answers",
                filter=Q(answers__student=request.user),
            ),
            correct_answers=Count(
                "answers",
                filter=Q(answers__student=request.user, answers__is_correct=True),
            ),
        )
        .prefetch_related("questions")
    )
    active_assignments = qs.filter(due_date__gte=now).order_by("due_date")
    past_assignments = qs.filter(due_date__lt=now).order_by("-due_date")

    return render(
        request,
        "assignments/student_assignments.html",
        {
            "course": course,
            "course_id": course_id,
            "active_assignments": active_assignments,
            "past_assignments": past_assignments,
            "nav_active": "courses",
        },
    )


@login_required
def professor_assignments(request, course_id: int):
    if not CourseProfessor.objects.filter(course_id=course_id, professor=request.user).exists():
        return redirect("/courses/")

    course = Course.objects.select_related("semester").get(id=course_id)
    now = timezone.now()

    qs = Assignment.objects.filter(course_id=course_id)
    active_assignments = qs.filter(due_date__gte=now).order_by("due_date")
    past_assignments = qs.filter(due_date__lt=now).order_by("-due_date")

    return render(
        request,
        "assignments/professor_assignments.html",
        {
            "course": course,
            "course_id": course_id,
            "active_assignments": active_assignments,
            "past_assignments": past_assignments,
            "nav_active": "courses",
        },
    )


@login_required
def create_assignment(request, course_id: int):
    if not CourseProfessor.objects.filter(course_id=course_id, professor=request.user).exists():
        return redirect("/courses/")

    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        description = (request.POST.get("description") or "").strip()
        due_date_raw = (request.POST.get("due_date") or "").strip()
        is_published = request.POST.get("is_published") == "on"

        if title and due_date_raw:
            # `datetime-local` comes without timezone; interpret in current timezone.
            naive_due = timezone.datetime.fromisoformat(due_date_raw)
            due_date = timezone.make_aware(naive_due, timezone.get_current_timezone())

            Assignment.objects.create(
                course=course,
                created_by=request.user,
                title=title,
                description=description,
                due_date=due_date,
                is_published=is_published,
            )

            return redirect(f"/assignments/{course_id}/professor/")

    return render(
        request,
        "assignments/create_assignment.html",
        {
            "course": course,
            "course_id": course_id,
            "assignment": None,
            "nav_active": "courses",
        },
    )


@login_required
def edit_assignment(request, course_id: int, assignment_id: int):
    if not CourseProfessor.objects.filter(course_id=course_id, professor=request.user).exists():
        return redirect("/courses/")

    assignment = get_object_or_404(Assignment, id=assignment_id, course_id=course_id)
    course = assignment.course

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        description = (request.POST.get("description") or "").strip()
        due_date_raw = (request.POST.get("due_date") or "").strip()
        is_published = request.POST.get("is_published") == "on"

        if title and due_date_raw:
            naive_due = timezone.datetime.fromisoformat(due_date_raw)
            due_date = timezone.make_aware(naive_due, timezone.get_current_timezone())

            assignment.title = title
            assignment.description = description
            assignment.due_date = due_date
            assignment.is_published = is_published
            assignment.save()

            return redirect(f"/assignments/{course_id}/professor/")

    return render(
        request,
        "assignments/create_assignment.html",
        {
            "course": course,
            "course_id": course_id,
            "assignment": assignment,
            "nav_active": "courses",
        },
    )


@login_required
def delete_assignment(request, course_id: int, assignment_id: int):
    if not CourseProfessor.objects.filter(course_id=course_id, professor=request.user).exists():
        return redirect("/courses/")

    assignment = get_object_or_404(Assignment, id=assignment_id, course_id=course_id)

    if request.method == "POST":
        assignment.delete()
        return redirect(f"/assignments/{course_id}/professor/")

    return redirect(f"/assignments/{course_id}/professor/")


@login_required
def generate_mcqs(request, course_id: int, assignment_id: int):
    if not CourseProfessor.objects.filter(course_id=course_id, professor=request.user).exists():
        return redirect("/courses/")

    assignment = get_object_or_404(Assignment, id=assignment_id, course_id=course_id)

    error = None
    if request.method == "POST":
        topic = (request.POST.get("topic") or "").strip()
        try:
            num_questions = int(request.POST.get("num_questions") or "5")
        except ValueError:
            num_questions = 5

        if num_questions < 1:
            num_questions = 1
        if num_questions > 20:
            num_questions = 20

        pdf_file = request.FILES.get("source_pdf")

        try:
            generate_mcqs_for_assignment(
                assignment=assignment,
                num_questions=num_questions,
                topic=topic,
                pdf_file=pdf_file,
            )
            return redirect(f"/assignments/{course_id}/professor/{assignment.id}/questions/")
        except Exception as exc:  # noqa: BLE001
            error = str(exc)

    return render(
        request,
        "assignments/generate_mcqs.html",
        {
            "course": assignment.course,
            "course_id": course_id,
            "assignment": assignment,
            "nav_active": "courses",
            "error": error,
        },
    )


@login_required
def assignment_questions(request, course_id: int, assignment_id: int):
    if not CourseProfessor.objects.filter(course_id=course_id, professor=request.user).exists():
        return redirect("/courses/")

    assignment = get_object_or_404(Assignment, id=assignment_id, course_id=course_id)
    questions = AssignmentQuestion.objects.filter(assignment=assignment, is_active=True)

    return render(
        request,
        "assignments/assignment_questions.html",
        {
            "course": assignment.course,
            "course_id": course_id,
            "assignment": assignment,
            "questions": questions,
            "nav_active": "courses",
        },
    )


@login_required
def assignment_results(request, course_id: int, assignment_id: int):
    if not CourseProfessor.objects.filter(course_id=course_id, professor=request.user).exists():
        return redirect("/courses/")

    assignment = get_object_or_404(Assignment, id=assignment_id, course_id=course_id)
    answers = (
        StudentAnswer.objects.filter(assignment=assignment)
        .select_related("student")
        .order_by("student__username")
    )

    stats = {}
    for ans in answers:
        s = stats.setdefault(
            ans.student_id,
            {"student": ans.student, "correct": 0, "total": 0},
        )
        s["total"] += 1
        if ans.is_correct:
            s["correct"] += 1

    results = []
    question_count = assignment.questions.count()
    for data in stats.values():
        total = data["total"]
        correct = data["correct"]
        percent = int(correct * 100 / question_count) if question_count else 0
        results.append(
            {
                "student": data["student"],
                "correct": correct,
                "total": question_count,
                "percent": percent,
            }
        )

    return render(
        request,
        "assignments/assignment_results.html",
        {
            "course": assignment.course,
            "course_id": course_id,
            "assignment": assignment,
            "results": results,
            "question_count": question_count,
            "nav_active": "courses",
        },
    )


@login_required
def student_take_assignment(request, course_id: int, assignment_id: int):
    if not CourseStudent.objects.filter(course_id=course_id, student=request.user).exists():
        return redirect("/courses/")

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        course_id=course_id,
        is_published=True,
    )
    questions = AssignmentQuestion.objects.filter(assignment=assignment, is_active=True)

    # Has this student already submitted?
    locked = StudentAnswer.objects.filter(
        assignment=assignment,
        student=request.user,
    ).exists()

    if request.method == "POST" and not locked:
        for q in questions:
            field_name = f"q_{q.id}"
            choice = request.POST.get(field_name)
            if not choice:
                continue
            is_correct = choice == q.correct_option
            StudentAnswer.objects.update_or_create(
                assignment=assignment,
                question=q,
                student=request.user,
                defaults={
                    "selected_option": choice,
                    "is_correct": is_correct,
                },
            )
        locked = True

    # Load answers and compute score
    answers = {
        a.question_id: a
        for a in StudentAnswer.objects.filter(
            assignment=assignment,
            student=request.user,
        )
    }
    # Attach answer object to each question for easier template access
    for q in questions:
        q.answer = answers.get(q.id)
    total = questions.count()
    correct = sum(
        1
        for q in questions
        if answers.get(q.id) and answers[q.id].is_correct
    )
    score = None
    if total and answers:
        score = int(correct * 100 / total)

    return render(
        request,
        "assignments/student_take_assignment.html",
        {
            "course": assignment.course,
            "course_id": course_id,
            "assignment": assignment,
            "questions": questions,
            "answers": answers,
            "total": total,
            "correct": correct,
            "score": score,
            "locked": locked,
            "nav_active": "courses",
        },
    )

