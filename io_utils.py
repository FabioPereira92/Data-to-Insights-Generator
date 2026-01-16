"""
CSV loading and output writing utilities.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def load_csv(path: Path) -> pd.DataFrame:
    """Load CSV into a pandas DataFrame with basic validations.

    Raises:
        FileNotFoundError: if file does not exist
        ValueError: if file has no rows or invalid column names
    """
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    df = pd.read_csv(path)

    if df.shape[0] < 1:
        raise ValueError("CSV must contain at least one row")

    if not all(isinstance(col, str) for col in df.columns):
        raise ValueError("All column names must be strings")

    return df


def write_insights(out_path: Path, insights: dict[str, Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)


def append_run_log(log_path: Path, entry: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logs: list[dict[str, Any]] = []
    if log_path.exists():
        try:
            with log_path.open("r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append(entry)
    with log_path.open("w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

