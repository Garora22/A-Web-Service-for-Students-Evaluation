from typing import List

from django.db import transaction

from courses.models import Course
from .models import Assignment, AssignmentQuestion
from .llm_client import generate_mcqs_with_ollama


def _build_simple_context(course: Course, topic: str) -> List[str]:
    pieces = [
        f"Course code: {course.code}",
        f"Course name: {course.name}",
    ]
    if topic:
        pieces.append(f"Topic for questions: {topic}")
    return ["\n".join(pieces)]


def generate_mcqs_for_assignment(
    assignment: Assignment,
    num_questions: int,
    topic: str,
) -> int:
    course = assignment.course
    context_chunks = _build_simple_context(course, topic)

    llm_questions = generate_mcqs_with_ollama(
        context_chunks=context_chunks,
        num_questions=num_questions,
    )

    created = 0
    with transaction.atomic():
        for q in llm_questions:
            options = q.get("options") or {}
            AssignmentQuestion.objects.create(
                assignment=assignment,
                question_text=q.get("question", ""),
                option_a=options.get("A", ""),
                option_b=options.get("B", ""),
                option_c=options.get("C", ""),
                option_d=options.get("D", ""),
                correct_option=q.get("correct", "A"),
                explanation=q.get("explanation", ""),
            )
            created += 1

    return created

