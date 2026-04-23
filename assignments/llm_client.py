import json
import os
from typing import List, Dict, Any

import requests


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:latest")


_JSON_SCHEMA_HINT = """
Respond in STRICT JSON with this structure:

{
  "questions": [
    {
      "question": "...",
      "options": {
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
      },
      "correct": "A",
      "explanation": "..."
    }
  ]
}

Do not include any text before or after the JSON.
"""


def _build_mcq_prompt(context_chunks: List[str], num_questions: int) -> str:
    context_text = "\n\n".join(context_chunks)

    return f"""You are a university instructor. Using ONLY the following material:

\"\"\"
{context_text}
\"\"\"

Generate exactly {num_questions} multiple-choice questions (MCQs).
Each question must have:
- a clear question stem
- exactly 4 options: A, B, C, D
- exactly one correct option
- a short explanation

{_JSON_SCHEMA_HINT}"""


def _build_mcq_prompt_from_source_document(
    context_chunks: List[str],
    num_questions: int,
) -> str:
    """Prompt when content comes from an uploaded PDF/slides—no course-name drift."""
    context_text = "\n\n".join(context_chunks)

    return f"""You write exam questions for university courses. The ONLY source you may use is the text between SOURCE_BEGIN and SOURCE_END below. Treat everything outside that block as rules, not as exam content.

Rules (must follow all):
1) Every question, every correct answer, every wrong option, and every explanation MUST be grounded in the SOURCE text only. If something is not stated or clearly implied in the SOURCE, do not ask about it.
2) Do NOT use course names, course codes, file names, or any general knowledge not present in the SOURCE. Do not invent facts.
3) Prefer questions that test understanding of definitions, steps, lists, diagrams described in words, comparisons, or conclusions that appear in the SOURCE.
4) Distractors (wrong options) should be plausible but still incorrect according to the SOURCE only.
5) If the SOURCE is short or sparse, ask fewer but simpler factual questions still strictly from the SOURCE (you must still output exactly {num_questions} questions, reusing different sentences/ideas from the SOURCE where needed).

SOURCE_BEGIN
{context_text}
SOURCE_END

Generate exactly {num_questions} MCQs. Output JSON only.

{_JSON_SCHEMA_HINT}"""


def generate_mcqs_with_ollama(
    context_chunks: List[str],
    num_questions: int = 5,
    *,
    from_source_document: bool = False,
) -> List[Dict[str, Any]]:
    if from_source_document:
        prompt = _build_mcq_prompt_from_source_document(context_chunks, num_questions)
    else:
        prompt = _build_mcq_prompt(context_chunks, num_questions)

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=900,
    )
    response.raise_for_status()

    data = response.json()
    raw_text = (data.get("response") or "").strip()

    if not raw_text:
        raise ValueError("Model returned an empty response. Is Ollama running and the model loaded?")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = raw_text[start : end + 1]
            parsed = json.loads(candidate)
        else:
            snippet = raw_text[:200].replace("\n", " ")
            raise ValueError(f"Model did not return valid JSON. Start of response: {snippet!r}")

    questions = parsed.get("questions", [])

    if not isinstance(questions, list):
        raise ValueError("Model response did not contain a 'questions' list.")

    return questions

