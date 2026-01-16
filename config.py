"""
Configuration and environment handling.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Load a local .env file if present (safe, only sets vars that are not already in the environment)
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    try:
        with _env_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # Do not overwrite existing environment variables
                os.environ.setdefault(key, val)
    except Exception:
        # Fail silently; environment variables may be set elsewhere
        pass


@dataclass
class Settings:
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")


__all__ = ["Settings"]
