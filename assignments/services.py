from typing import List, Optional, Sequence, Tuple

from django.db import transaction

from content.models import CourseMaterial, CourseMaterialText
from courses.models import Course
from .llm_client import generate_mcqs_with_ollama
from .models import Assignment, AssignmentQuestion
from .material_text import extract_text_from_material
from .pdf_text import chunk_text


def _instruction_chunk_source_materials(
    topic: str,
    professor_comment: str,
) -> str:
    lines = [
        "INSTRUCTIONS (not exam content): Questions must come only from the course material excerpts that follow.",
        "Do not use course titles, codes, or unstated general knowledge.",
    ]
    if professor_comment.strip():
        lines.append(
            f"Instructor note (guidance only, not extra facts to test): {professor_comment.strip()}"
        )
    if topic.strip():
        lines.append(
            f"Optional focus: prioritize ideas related to «{topic.strip()}» only where they appear in those excerpts."
        )
    return "\n".join(lines)


def _combined_text_from_materials(
    course_id: int,
    material_ids: Sequence[int],
) -> str:
    """Load and concatenate extractable text from selected course materials."""
    if not material_ids:
        raise ValueError("Select at least one file from course materials.")

    qs = CourseMaterial.objects.filter(course_id=course_id, id__in=material_ids).order_by(
        "uploaded_at", "id"
    )
    found_ids = set(qs.values_list("id", flat=True))
    if found_ids != set(material_ids):
        raise ValueError("One or more selected materials are invalid for this course.")

    parts: List[str] = []
    unsupported: List[str] = []
    for m in qs:
        cached = getattr(m, "extracted_text", None)
        if cached and cached.status == "ok" and cached.text.strip():
            parts.append(f"=== {m.title} ({m.content_type}/{cached.kind}) ===\n{cached.text.strip()}")
            continue

        # Fallback: extract on the fly (for older uploads that haven't been cached yet)
        filename = m.file.name or ""
        try:
            with m.file.open("rb") as f:
                text, kind = extract_text_from_material(filename, f)
            CourseMaterialText.objects.update_or_create(
                material=m,
                defaults={
                    "file_name": filename,
                    "kind": kind,
                    "text": text,
                    "status": "ok" if text.strip() else "error",
                    "error_message": "" if text.strip() else "Empty extracted text",
                    "extractor_version": "v1",
                },
            )
        except RuntimeError:
            raise
        except ValueError as exc:
            unsupported.append(f"• {m.title} ({filename}): {exc}")
            CourseMaterialText.objects.update_or_create(
                material=m,
                defaults={
                    "file_name": filename,
                    "kind": "",
                    "text": "",
                    "status": "unsupported",
                    "error_message": str(exc),
                    "extractor_version": "v1",
                },
            )
            continue
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Could not read «{m.title}»: {exc}") from exc

        if text.strip():
            parts.append(f"=== {m.title} ({m.content_type}/{kind}) ===\n{text.strip()}")

    if not parts:
        if unsupported:
            raise ValueError(
                "None of the selected materials could be used.\n"
                "Unsupported files:\n"
                + "\n".join(unsupported[:8])
            )
        raise ValueError(
            "No text could be extracted from the selected files. "
            "Use text-based PDFs or PPTX (not scanned images), or select different materials."
        )

    return "\n\n".join(parts)


def _split_counts(total: int) -> Tuple[int, int, int]:
    """
    40% easy (1 mark), 30% medium (2 marks), 30% hard (4 marks).
    Rounds to ensure sum == total and at least 1 question if total > 0.
    """
    easy = round(total * 0.4)
    medium = round(total * 0.3)
    hard = total - easy - medium
    if total > 0 and (easy + medium + hard) != total:
        hard = max(0, total - easy - medium)
    if total > 0 and (easy, medium, hard) == (0, 0, 0):
        easy = total
    # ensure no negatives
    if hard < 0:
        hard = 0
        # push remainder into easy
        easy = total - medium
    return easy, medium, hard


def _build_context_chunks(
    course: Course,
    topic: str,
    professor_comment: str,
    material_ids: Optional[Sequence[int]],
) -> Tuple[List[str], bool]:
    """
    Returns (chunks, from_source_document).
    When course PDF materials are selected, excerpts are used; course name/code omitted.
    """
    if material_ids:
        combined = _combined_text_from_materials(course.id, list(material_ids))
        pdf_chunks = chunk_text(combined, max_size=4500, max_chunks=20)
        chunks: List[str] = [
            _instruction_chunk_source_materials(topic, professor_comment),
        ]
        n = len(pdf_chunks)
        for i, pc in enumerate(pdf_chunks, start=1):
            chunks.append(f"[Document excerpt {i}/{n} — sole source for MCQs]\n{pc}")
        return chunks, True

    # No materials: topic + course metadata (legacy behavior)
    header_parts = [
        f"Course code: {course.code}",
        f"Course name: {course.name}",
    ]
    if topic.strip():
        header_parts.append(f"Topic for questions: {topic.strip()}")
    if professor_comment.strip():
        header_parts.append(f"Instructor note: {professor_comment.strip()}")

    return ["\n".join(header_parts)], False


def generate_mcqs_for_assignment(
    assignment: Assignment,
    num_questions: int,
    topic: str,
    professor_comment: str = "",
    material_ids: Optional[Sequence[int]] = None,
) -> int:
    course = assignment.course
    context_chunks, from_source_document = _build_context_chunks(
        course,
        topic,
        professor_comment,
        material_ids,
    )
    easy_n, medium_n, hard_n = _split_counts(num_questions)
    # generate 2x pool, then downsample to target counts (keeps difficulty split)
    pool_easy, pool_medium, pool_hard = easy_n * 2, medium_n * 2, hard_n * 2
    llm_questions: List[dict] = []
    if pool_easy:
        qs = generate_mcqs_with_ollama(
            context_chunks=context_chunks + [f"DIFFICULTY: easy (basic recall/definition)"],
            num_questions=pool_easy,
            from_source_document=from_source_document,
        )
        for q in qs:
            q["_difficulty"] = "easy"
            q["_marks"] = 1
        llm_questions.extend(qs)
    if pool_medium:
        qs = generate_mcqs_with_ollama(
            context_chunks=context_chunks + [f"DIFFICULTY: medium (conceptual understanding/application)"],
            num_questions=pool_medium,
            from_source_document=from_source_document,
        )
        for q in qs:
            q["_difficulty"] = "medium"
            q["_marks"] = 2
        llm_questions.extend(qs)
    if pool_hard:
        qs = generate_mcqs_with_ollama(
            context_chunks=context_chunks + [f"DIFFICULTY: hard (tricky/edge cases, deeper reasoning)"],
            num_questions=pool_hard,
            from_source_document=from_source_document,
        )
        for q in qs:
            q["_difficulty"] = "hard"
            q["_marks"] = 4
        llm_questions.extend(qs)

    # Deduplicate by question text (best-effort), then sample per difficulty back to target counts
    from collections import defaultdict
    import random

    buckets = defaultdict(list)
    seen = set()
    for q in llm_questions:
        qt = (q.get("question") or "").strip()
        key = (q.get("_difficulty"), qt.lower())
        if not qt or key in seen:
            continue
        seen.add(key)
        buckets[q.get("_difficulty")].append(q)

    rnd = random.Random(f"{assignment.id}:{timezone.now().timestamp()}")
    final = []
    for diff, n in (("easy", easy_n), ("medium", medium_n), ("hard", hard_n)):
        items = buckets.get(diff, [])
        if len(items) <= n:
            final.extend(items)
        else:
            final.extend(rnd.sample(items, n))

    llm_questions = final

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
                difficulty=q.get("_difficulty", "easy"),
                marks=int(q.get("_marks", 1)),
            )
            created += 1

    return created

