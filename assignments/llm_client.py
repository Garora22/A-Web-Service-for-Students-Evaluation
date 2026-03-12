import json
import os
from typing import List, Dict, Any

import requests


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3")


def _build_mcq_prompt(context_chunks: List[str], num_questions: int) -> str:
    context_text = "\n\n".join(context_chunks)

    return f"""
You are a university instructor. Using ONLY the following course material:

\"\"\" 
{context_text}
\"\"\"

Generate exactly {num_questions} multiple-choice questions (MCQs).
Each question must have:
- a clear question stem
- exactly 4 options: A, B, C, D
- exactly one correct option
- a short explanation

Respond in STRICT JSON with this structure:

{{
  "questions": [
    {{
      "question": "...",
      "options": {{
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
      }},
      "correct": "A",
      "explanation": "..."
    }}
  ]
}}

Do not include any text before or after the JSON.
"""


def generate_mcqs_with_ollama(
    context_chunks: List[str],
    num_questions: int = 5,
) -> List[Dict[str, Any]]:
    prompt = _build_mcq_prompt(context_chunks, num_questions)

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()

    data = response.json()
    raw_text = (data.get("response") or "").strip()

    if not raw_text:
        raise ValueError("Model returned an empty response. Is Ollama running and the model loaded?")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to recover if the model wrapped JSON in text or code fences
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

