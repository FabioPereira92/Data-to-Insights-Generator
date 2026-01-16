"""
Prompt templates for LLM interaction.
"""
from __future__ import annotations
from typing import Any


def build_prompt(schema: list[dict[str, str]], sample_rows: list[dict[str, Any]], stats: dict[str, Any], question: str) -> str:
    """Construct a prompt that includes schema, samples, stats, and the user's question.

    The prompt instructs the model to return strict JSON conforming to the project's schema.
    """
    prompt = (
        "You are a data analyst assistant. Do NOT return any explanation outside of the JSON object.\n"
        "Return STRICT JSON with the following keys: executive_summary, key_insights, suggested_charts, analysis_notes, limitations.\n"
        "Respond in JSON only.\n\n"
        "Dataset schema:\n"
        f"{schema}\n\n"
        "Sample rows:\n"
        f"{sample_rows}\n\n"
        "Summary statistics (describe):\n"
        f"{stats}\n\n"
        "User question:\n"
        f"{question}\n\n"
        "Notes:\n"
        "- Do not attempt to run code.\n"
        "- Keep outputs concise and factual.\n"
        "- When suggesting charts, include chart_type, columns, and reason.\n"
    )
    return prompt

