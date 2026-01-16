"""
AI Data-to-Insights Generator - CLI entrypoint
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

from config import Settings
from io_utils import load_csv, write_insights, append_run_log
from analysis import summarize_df
from llm import LLMClient
from prompts import build_prompt
from schemas import validate_output_schema


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a CSV dataset into structured insights using an LLM."
    )
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--question", required=True, help="Natural-language question about the data")
    parser.add_argument(
        "--model",
        default=Settings.DEFAULT_MODEL,
        help=f"LLM model to use (default: {Settings.DEFAULT_MODEL})",
    )
    parser.add_argument("--out", default="./output", help="Output directory (default: ./output)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without calling the OpenAI API; write deterministic fake output",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    input_path = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        df = load_csv(input_path)
    except Exception as exc:
        print(f"Error loading CSV: {exc}", file=sys.stderr)
        return 2

    summary = summarize_df(df)

    prompt = build_prompt(
        schema=summary["schema"],
        sample_rows=summary["head"],
        stats=summary["describe"],
        question=args.question,
    )

    client = LLMClient(api_key=Settings.OPENAI_API_KEY)

    response_json: dict[str, Any]
    try:
        response_json, token_estimate, cost_estimate = client.analyze(
            prompt=prompt, model=args.model, dry_run=bool(args.dry_run)
        )
    except Exception as exc:
        print(f"LLM error: {exc}", file=sys.stderr)
        return 3

    # Validate LLM output schema
    valid, errors = validate_output_schema(response_json)
    if not valid:
        print("Warning: LLM output failed schema validation:", errors, file=sys.stderr)

    insights_path = out_dir / "insights.json"
    write_insights(insights_path, response_json)

    # Append run log
    run_log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_file": str(input_path),
        "question": args.question,
        "model": args.model,
        "row_count": summary["row_count"],
        "estimated_tokens": token_estimate,
        "estimated_cost_usd": cost_estimate,
    }
    append_run_log(out_dir / "run_log.json", run_log_entry)

    print(f"Insights written to: {insights_path}")
    print(f"Run log appended to: {out_dir / 'run_log.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
