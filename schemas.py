"""
JSON schema validation for LLM outputs.
"""
from __future__ import annotations

from typing import Any, Tuple
import jsonschema


OUTPUT_SCHEMA = {
    "type": "object",
    "required": [
        "executive_summary",
        "key_insights",
        "suggested_charts",
        "analysis_notes",
        "limitations",
    ],
    "properties": {
        "executive_summary": {"type": "string"},
        "key_insights": {"type": "array", "items": {"type": "string"}},
        "suggested_charts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["chart_type", "columns", "reason"],
                "properties": {
                    "chart_type": {"type": "string"},
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
            },
        },
        "analysis_notes": {"type": "string"},
        "limitations": {"type": "string"},
    },
}


def validate_output_schema(obj: Any) -> Tuple[bool, list[str]]:
    try:
        jsonschema.validate(instance=obj, schema=OUTPUT_SCHEMA)
        return True, []
    except jsonschema.ValidationError as exc:
        return False, [str(exc)]

