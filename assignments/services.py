import random
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

from django.db import transaction
from django.utils import timezone

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


def _assign_difficulties_to_pool(pool: List[Dict]) -> List[Tuple[Dict, str, int]]:
    """
    Assign difficulty levels to a pool of questions.
    Distributes difficulties evenly across the pool: 40% easy, 30% medium, 30% hard.
    
    Returns list of (question_dict, difficulty, marks) tuples.
    """
    pool_size = len(pool)
    easy_count, medium_count, hard_count = _split_counts(pool_size)
    
    # Create list of (difficulty, marks) tuples
    difficulty_marks = (
        [("easy", 1)] * easy_count
        + [("medium", 2)] * medium_count
        + [("hard", 4)] * hard_count
    )
    
    # Shuffle to randomly distribute difficulties
    random.shuffle(difficulty_marks)
    
    result = []
    for i, q in enumerate(pool):
        diff, marks = difficulty_marks[i] if i < len(difficulty_marks) else ("easy", 1)
        result.append((q, diff, marks))
    
    return result


def select_questions_for_student(
    all_questions: List[AssignmentQuestion],
    num_to_select: int,
) -> List[AssignmentQuestion]:
    """
    Select a random subset of questions while maintaining difficulty ratio.
    
    Args:
        all_questions: All available questions from the pool
        num_to_select: Number of questions to select (typically 5)
    
    Returns: List of selected questions maintaining the 40/30/30 difficulty ratio
    """
    # Calculate target difficulty distribution
    target_easy, target_medium, target_hard = _split_counts(num_to_select)
    
    # Group questions by difficulty
    by_difficulty: Dict[str, List[AssignmentQuestion]] = defaultdict(list)
    for q in all_questions:
        by_difficulty[q.difficulty].append(q)
    
    # Randomly select from each difficulty level
    selected = []
    if target_easy > 0 and by_difficulty["easy"]:
        selected.extend(random.sample(
            by_difficulty["easy"],
            min(target_easy, len(by_difficulty["easy"]))
        ))
    if target_medium > 0 and by_difficulty["medium"]:
        selected.extend(random.sample(
            by_difficulty["medium"],
            min(target_medium, len(by_difficulty["medium"]))
        ))
    if target_hard > 0 and by_difficulty["hard"]:
        selected.extend(random.sample(
            by_difficulty["hard"],
            min(target_hard, len(by_difficulty["hard"]))
        ))
    
    return selected


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
    """
    Generate MCQs for an assignment.
    
    Generates 2x the requested questions and saves all to the pool.
    - Professor sees all questions
    - When students take the assignment, 5 will be randomly selected from the pool
    
    Args:
        assignment: The assignment to create questions for
        num_questions: Number of questions to request (system will generate 2x)
        topic: Topic for the questions
        professor_comment: Instructor comment
        material_ids: IDs of course materials to use
    
    Returns: Number of questions created
    """
    course = assignment.course
    context_chunks, from_source_document = _build_context_chunks(
        course,
        topic,
        professor_comment,
        material_ids,
    )
    
    # Always generate 2x the requested amount for the pool
    llm_request_count = num_questions * 2
    
    # Calculate difficulty distribution across the FULL pool
    pool_easy, pool_medium, pool_hard = _split_counts(llm_request_count)

    print(f"[DEBUG] Requesting {llm_request_count} questions from LLM (pool size)")

    # Single Ollama call for all questions
    llm_questions: List[dict] = generate_mcqs_with_ollama(
        context_chunks=context_chunks,
        num_questions=llm_request_count,
        from_source_document=from_source_document,
    )

    print(f"[DEBUG] Received {len(llm_questions)} questions from LLM")

    # Deduplicate by question text
    seen: set = set()
    unique: List[dict] = []
    for q in llm_questions:
        qt = (q.get("question") or "").strip().lower()
        if qt and qt not in seen:
            seen.add(qt)
            unique.append(q)

    print(f"[DEBUG] After deduplication: {len(unique)} unique questions")

    # Assign difficulties to all questions in the pool
    pool_with_difficulties = _assign_difficulties_to_pool(unique)
    
    print(f"[DEBUG] Saving all {len(pool_with_difficulties)} questions to database (professor will see all)")

    created = 0
    with transaction.atomic():
        for q, diff, marks in pool_with_difficulties:
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
                difficulty=diff,
                marks=marks,
                is_active=True,
            )
            created += 1

    print(f"[DEBUG] Created {created} questions total (students will see random subset of {num_questions})")
    return created

