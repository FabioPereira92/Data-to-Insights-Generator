"""
Pandas analysis helpers for extracting schema, samples, and stats.
"""
from __future__ import annotations

from typing import Any
import pandas as pd


def summarize_df(df: pd.DataFrame) -> dict[str, Any]:
    """Return a summary including schema, head, describe, and row count.

    The schema contains column names and inferred dtypes.
    """
    schema = [{"column": col, "dtype": str(dtype)} for col, dtype in zip(df.columns, df.dtypes)]
    head = df.head(5).to_dict(orient="records")
    try:
        describe = df.describe(include="all").fillna("").to_dict()
    except Exception:
        describe = {}

    return {
        "schema": schema,
        "head": head,
        "describe": describe,
        "row_count": int(df.shape[0]),
    }

