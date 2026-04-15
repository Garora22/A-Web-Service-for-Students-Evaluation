from typing import List, Optional

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from courses.models import Course
from .llm_client import generate_mcqs_with_ollama
from .models import Assignment, AssignmentQuestion
from .pdf_text import chunk_text, extract_text_from_pdf


def _build_simple_context(course: Course, topic: str) -> List[str]:
    pieces = [
        f"Course code: {course.code}",
        f"Course name: {course.name}",
    ]
    if topic:
        pieces.append(f"Topic for questions: {topic}")
    return ["\n".join(pieces)]


def _instruction_chunk_pdf_only(topic: str) -> str:
    lines = [
        "INSTRUCTIONS (not exam content): Questions must come only from the PDF excerpts that follow.",
        "Do not use course titles, codes, or unstated general knowledge.",
    ]
    if topic.strip():
        lines.append(
            f"Optional focus: prioritize ideas related to «{topic.strip()}» only where they appear in those excerpts."
        )
    return "\n".join(lines)


def _build_context_chunks(
    course: Course,
    topic: str,
    pdf_file: Optional[UploadedFile],
) -> tuple[List[str], bool]:
    """
    Returns (chunks, from_source_document).
    When a PDF is uploaded, course name/code is omitted to avoid the model
    anchoring on them; excerpts are placed first after a short instruction block.
    """
    if pdf_file:
        name = getattr(pdf_file, "name", "") or ""
        if not name.lower().endswith(".pdf"):
            raise ValueError("Please upload a PDF file (.pdf).")
        try:
            pdf_text = extract_text_from_pdf(pdf_file)
        except RuntimeError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Could not read PDF: {exc}") from exc
        if not pdf_text.strip():
            raise ValueError(
                "No extractable text found in this PDF. It may be scanned images only."
            )
        pdf_chunks = chunk_text(pdf_text, max_size=4500, max_chunks=12)
        chunks: List[str] = [
            _instruction_chunk_pdf_only(topic),
        ]
        n = len(pdf_chunks)
        for i, pc in enumerate(pdf_chunks, start=1):
            chunks.append(f"[Document excerpt {i}/{n} — sole source for MCQs]\n{pc}")
        return chunks, True

    # No PDF: topic + course metadata (legacy behavior)
    header_parts = [
        f"Course code: {course.code}",
        f"Course name: {course.name}",
    ]
    if topic.strip():
        header_parts.append(f"Topic for questions: {topic.strip()}")

    return ["\n".join(header_parts)], False


def generate_mcqs_for_assignment(
    assignment: Assignment,
    num_questions: int,
    topic: str,
    pdf_file: Optional[UploadedFile] = None,
) -> int:
    course = assignment.course
    context_chunks, from_source_document = _build_context_chunks(course, topic, pdf_file)

    llm_questions = generate_mcqs_with_ollama(
        context_chunks=context_chunks,
        num_questions=num_questions,
        from_source_document=from_source_document,
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

