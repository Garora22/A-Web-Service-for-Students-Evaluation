from __future__ import annotations

from .models import CourseMaterial, CourseMaterialText
from assignments.material_text import extract_text_from_material


def extract_and_cache_material_text(material: CourseMaterial) -> CourseMaterialText:
    filename = material.file.name or ""
    try:
        with material.file.open("rb") as f:
            text, kind = extract_text_from_material(filename, f)
        status = "ok"
        error_message = ""
    except ValueError as exc:
        text = ""
        kind = ""
        status = "unsupported"
        error_message = str(exc)
    except Exception as exc:  
        text = ""
        kind = ""
        status = "error"
        error_message = str(exc)

    obj, _ = CourseMaterialText.objects.update_or_create(
        material=material,
        defaults={
            "file_name": filename,
            "kind": kind,
            "text": text,
            "status": status,
            "error_message": error_message,
            "extractor_version": "v1",
        },
    )
    return obj

