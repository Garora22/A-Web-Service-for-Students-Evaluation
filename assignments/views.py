from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from content.models import CourseMaterial
from courses.models import Course, CourseProfessor, CourseStudent, CourseTA

import hashlib
import random

from django.utils import timezone as dj_timezone

from .models import Assignment, AssignmentQuestion, StudentAnswer, StudentAttempt
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
        try:
            duration_minutes = int(request.POST.get("duration_minutes") or "20")
        except ValueError:
            duration_minutes = 20
        duration_minutes = max(1, min(duration_minutes, 300))

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
                duration_minutes=duration_minutes,
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
        try:
            duration_minutes = int(request.POST.get("duration_minutes") or str(assignment.duration_minutes))
        except ValueError:
            duration_minutes = assignment.duration_minutes
        duration_minutes = max(1, min(duration_minutes, 300))

        if title and due_date_raw:
            naive_due = timezone.datetime.fromisoformat(due_date_raw)
            due_date = timezone.make_aware(naive_due, timezone.get_current_timezone())

            assignment.title = title
            assignment.description = description
            assignment.due_date = due_date
            assignment.is_published = is_published
            assignment.duration_minutes = duration_minutes
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
    course = assignment.course
    materials = list(
        CourseMaterial.objects.filter(course_id=course_id).order_by("-uploaded_at", "title")
    )

    if request.method == "POST":
        topic = (request.POST.get("topic") or "").strip()
        professor_comment = (request.POST.get("professor_comment") or "").strip()
        material_ids: list[int] = []
        for raw in request.POST.getlist("material_ids"):
            try:
                material_ids.append(int(raw))
            except ValueError:
                continue
        try:
            num_questions = int(request.POST.get("num_questions") or "5")
        except ValueError:
            num_questions = 5

        if num_questions < 1:
            num_questions = 1
        if num_questions > 20:
            num_questions = 20

        try:
            generate_mcqs_for_assignment(
                assignment=assignment,
                num_questions=num_questions,
                topic=topic,
                professor_comment=professor_comment,
                material_ids=material_ids if material_ids else None,
            )
            return redirect(f"/assignments/{course_id}/professor/{assignment.id}/questions/")
        except Exception as exc:  # noqa: BLE001
            error = str(exc)

    return render(
        request,
        "assignments/generate_mcqs.html",
        {
            "course": course,
            "course_id": course_id,
            "assignment": assignment,
            "materials": materials,
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

    attempts = (
        StudentAttempt.objects.filter(assignment=assignment)
        .select_related("student")
        .order_by("student__username")
    )

    total_marks = sum(
        q.marks for q in AssignmentQuestion.objects.filter(assignment=assignment, is_active=True)
    )

    results = []
    for att in attempts:
        percent = int(att.score * 100 / total_marks) if total_marks else 0
        results.append(
            {
                "student": att.student,
                "earned": att.score,
                "total_marks": total_marks,
                "percent": percent,
                "submitted_at": att.submitted_at,
                "time_taken_min": (
                    int((att.submitted_at - att.started_at).total_seconds() / 60)
                    if att.submitted_at
                    else None
                ),
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
            "total_marks": total_marks,
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
    questions_qs = AssignmentQuestion.objects.filter(assignment=assignment, is_active=True)

    # Create (or load) single attempt per student; this also gives us a stable seed for shuffling
    attempt = StudentAttempt.objects.filter(assignment=assignment, student=request.user).first()
    if not attempt:
        seed_src = f"{assignment.id}:{request.user.id}:{timezone.now().timestamp()}"
        seed = hashlib.sha256(seed_src.encode("utf-8")).hexdigest()[:32]
        expires_at = dj_timezone.now() + dj_timezone.timedelta(minutes=assignment.duration_minutes)
        attempt = StudentAttempt.objects.create(
            assignment=assignment,
            student=request.user,
            expires_at=expires_at,
            seed=seed,
            total_marks=0,
            score=0,
        )

    now = dj_timezone.now()
    time_up = now >= attempt.expires_at
    submitted = attempt.submitted_at is not None
    locked = submitted or time_up

    # Determine shuffled question order per attempt
    questions = list(questions_qs)
    rnd = random.Random(attempt.seed)
    rnd.shuffle(questions)

    # Determine shuffled options per question (value remains original letter)
    for q in questions:
        opts = [("A", q.option_a), ("B", q.option_b), ("C", q.option_c), ("D", q.option_d)]
        rnd2 = random.Random(f"{attempt.seed}:{q.id}")
        rnd2.shuffle(opts)
        q.shuffled_options = opts

    if request.method == "POST" and not locked:
        total_marks = 0
        score = 0
        for q in questions:
            field_name = f"q_{q.id}"
            choice = request.POST.get(field_name)
            if not choice:
                continue
            is_correct = choice == q.correct_option
            total_marks += q.marks
            if is_correct:
                score += q.marks
            StudentAnswer.objects.update_or_create(
                assignment=assignment,
                question=q,
                student=request.user,
                defaults={
                    "selected_option": choice,
                    "is_correct": is_correct,
                },
            )

        attempt.total_marks = total_marks
        attempt.score = score
        attempt.submitted_at = dj_timezone.now()
        attempt.save()
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
    total_questions = len(questions)
    total_marks = sum(q.marks for q in questions)
    earned_marks = sum(q.marks for q in questions if q.answer and q.answer.is_correct)
    percent = None
    if total_marks and answers:
        percent = int(earned_marks * 100 / total_marks)

    return render(
        request,
        "assignments/student_take_assignment.html",
        {
            "course": assignment.course,
            "course_id": course_id,
            "assignment": assignment,
            "questions": questions,
            "answers": answers,
            "total_questions": total_questions,
            "total_marks": total_marks,
            "earned_marks": earned_marks,
            "percent": percent,
            "locked": locked,
            "attempt": attempt,
            "time_up": time_up,
            "nav_active": "courses",
        },
    )

