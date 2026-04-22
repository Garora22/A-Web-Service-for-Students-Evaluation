from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from content.models import CourseMaterial
from courses.models import Course, CourseProfessor, CourseStudent, CourseTA

import hashlib
import random
from collections import defaultdict

from django.utils import timezone as dj_timezone

from .models import Assignment, AssignmentQuestion, StudentAnswer, StudentAttempt
from .services import generate_mcqs_for_assignment, select_questions_for_student


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
    attempts = StudentAttempt.objects.filter(
        student=request.user, 
        assignment__course_id=course_id
    )
    attempt_map = {att.assignment_id: att for att in attempts}

    # 2. Evaluate QuerySets to lists
    active_assignments = list(active_assignments)
    past_assignments = list(past_assignments)

    # 3. Attach the exact subset marks
    for a in active_assignments + past_assignments:
        att = attempt_map.get(a.id)
        
        if att and att.submitted_at:
            # If submitted, use the EXACT total from their specific random subset
            a.earned_marks = att.score
            a.total_marks = att.total_marks
        else:
            # If not submitted, calculate how many questions they WILL get based on your logic
            pool_size = len(a.questions.all())
            if pool_size > 0:
                num_to_select = min(5, max(1, pool_size // 2))
                
                # Assuming standard MCQ (all questions have equal marks)
                avg_marks = sum(q.marks for q in a.questions.all()) / pool_size
                a.total_marks = int(num_to_select * avg_marks)
            else:
                a.total_marks = 0
            
            a.earned_marks = 0

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

    # Calculate statistics
    total_questions = questions.count()
    easy_count = questions.filter(difficulty="easy").count()
    medium_count = questions.filter(difficulty="medium").count()
    hard_count = questions.filter(difficulty="hard").count()

    return render(
        request,
        "assignments/assignment_questions.html",
        {
            "course": assignment.course,
            "course_id": course_id,
            "assignment": assignment,
            "questions": questions,
            "total_questions": total_questions,
            "easy_count": easy_count,
            "medium_count": medium_count,
            "hard_count": hard_count,
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

    # This represents the total marks of ALL questions in the pool.
    # We keep it just in case your HTML template uses it for a header (e.g. "Question Pool Marks: 50")
    pool_total_marks = sum(
        q.marks for q in AssignmentQuestion.objects.filter(assignment=assignment, is_active=True)
    )

    results = []
    for att in attempts:
        # FIX: Calculate percentage based on the exact marks this student was tested on
        percent = int(att.score * 100 / att.total_marks) if att.total_marks else 0
        
        results.append(
            {
                "student": att.student,
                "earned": att.score,
                "total_marks": att.total_marks,  # FIX: Use their specific subset total
                "percent": percent,
                "submitted_at": att.submitted_at,
                "time_taken_min": (
                    int((att.submitted_at - att.started_at).total_seconds() / 60)
                    if att.submitted_at and hasattr(att, 'started_at') and att.started_at
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
            "total_marks": pool_total_marks, # Kept so your template doesn't break
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

    # Select subset of questions for this student (5 from the pool)
    # Use attempt seed to make selection deterministic per student but different per student
    all_questions = list(questions_qs)
    
    # Use seeded random to select questions
    rnd_selector = random.Random(attempt.seed)
    
    # Calculate how many questions to select (default 5, or half the pool if pool is smaller)
    num_to_select = min(5, max(1, len(all_questions) // 2))
    
    # Group by difficulty to maintain ratio
    by_difficulty: Dict[str, List[AssignmentQuestion]] = defaultdict(list)
    for q in all_questions:
        by_difficulty[q.difficulty].append(q)
    
    # Calculate target distribution
    target_easy = round(num_to_select * 0.4)
    target_medium = round(num_to_select * 0.3)
    target_hard = num_to_select - target_easy - target_medium
    
    # Randomly select maintaining ratio
    selected_questions = []
    if target_easy > 0:
        sample = rnd_selector.sample(
            by_difficulty.get("easy", []),
            min(target_easy, len(by_difficulty.get("easy", [])))
        )
        selected_questions.extend(sample)
    
    if target_medium > 0:
        sample = rnd_selector.sample(
            by_difficulty.get("medium", []),
            min(target_medium, len(by_difficulty.get("medium", [])))
        )
        selected_questions.extend(sample)
    
    if target_hard > 0:
        sample = rnd_selector.sample(
            by_difficulty.get("hard", []),
            min(target_hard, len(by_difficulty.get("hard", [])))
        )
        selected_questions.extend(sample)

    # Determine shuffled question order per attempt
    questions = selected_questions
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

