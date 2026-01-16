"""
OpenAI API wrapper using the Responses API style.

Implements:
- analyze(prompt, model, dry_run)

Dry-run returns deterministic fake output.
"""
from __future__ import annotations

import json
import re
import ast
from typing import Any, Tuple

from config import Settings


class LLMClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or Settings.OPENAI_API_KEY

    def _extract_json_substring(self, text: str) -> str | None:
        """Try to extract the first JSON object substring from a noisy string.

        Returns the JSON substring if found, otherwise None.
        """
        if not text:
            return None

        # Helper: extract balanced JSON object starting from a left brace
        def _balanced_from(start_idx: int) -> str | None:
            depth = 0
            in_str = False
            esc = False
            for i in range(start_idx, len(text)):
                ch = text[i]
                if ch == '"' and not esc:
                    in_str = not in_str
                if in_str and ch == '\\' and not esc:
                    esc = True
                    continue
                esc = False
                if not in_str:
                    if ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            return text[start_idx:i + 1]
            return None

        # 1) Look for a JSON object that contains the key "executive_summary" (likely the desired object)
        # Try a regex that captures an object containing the anchor (greedy to the closing brace)
        m_anchor = re.search(r'(\{[\s\S]*"executive_summary"[\s\S]*\})', text, re.S)
        if m_anchor:
            frag = m_anchor.group(1)
            # If the fragment is itself quoted (e.g., "{...}" or '{...}'), unquote it to get valid JSON
            frag_stripped = frag
            if (frag_stripped.startswith("'") and frag_stripped.endswith("'")) or (
                frag_stripped.startswith('"') and frag_stripped.endswith('"')
            ):
                try:
                    frag_stripped = ast.literal_eval(frag_stripped)
                except Exception:
                    # fall back to raw fragment
                    pass
            return frag_stripped

        # 2) First, try to find a JSON object that uses double-quoted keys (most likely valid JSON)
        m = re.search(r'(\{\s*"[^"\n]+"\s*:\s*[\s\S]*?\})', text, re.S)
        if m:
            return m.group(1)

        # 3) Next, try to extract an inner 'text' field from a Python-style repr like "{'text': '{\"k\": \"v\"}'}" or "\"text\": \"{...}\""
        m2 = re.search(r"'text'\s*:\s*(?P<quoted>'(?:\\.|[^'])*')", text, re.S)
        if m2:
            quoted = m2.group('quoted')
            try:
                inner = ast.literal_eval(quoted)  # safely evaluate the Python string literal
                return inner
            except Exception:
                # fall through to other heuristics
                pass
        m3 = re.search(r'"text"\s*:\s*"(?P<inner>\\?\{[\s\S]*?\\?\})"', text, re.S)
        if m3:
            # unescape surrounding quotes/backslashes if present
            inner = m3.group('inner')
            inner = inner.replace('\\n', '\n').replace('\\"', '"')
            return inner

        # Fallback: find the first balanced braces block that looks like an object
        m4 = re.search(r"(\{[\s\S]*?\})", text, re.S)
        if m4:
            return m4.group(1)
        return None

    def analyze(self, prompt: str, model: str = "gpt-4o-mini", dry_run: bool = False) -> Tuple[dict[str, Any], int, float]:
        """Send prompt to LLM and return parsed JSON, estimated tokens, and rough cost in USD.

        If dry_run is True, return deterministic fake output without calling any external API.
        """
        if dry_run:
            fake = {
                "executive_summary": "Revenue dropped in Q3 primarily due to seasonal decline and lower repeat purchases.",
                "key_insights": [
                    "Quarter-over-quarter revenue decreased by 12%",
                    "Top product category saw a 20% drop in units sold",
                ],
                "suggested_charts": [
                    {"chart_type": "line", "columns": ["date", "revenue"], "reason": "Trend over time shows Q3 drop"},
                    {"chart_type": "bar", "columns": ["product_category", "units_sold"], "reason": "Compare category performance"},
                ],
                "analysis_notes": "Recommend checking marketing spend and returns data; consider cohort analysis.",
                "limitations": "Analysis is based on summary stats and sample rows; full data may reveal different patterns.",
            }
            return fake, 50, 0.0025

        # Minimal external API interaction: use requests to call OpenAI Responses API if key present.
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured. Set OPENAI_API_KEY or use --dry-run")

        # For this project we avoid adding an external OpenAI SDK dependency; instead we make a simple HTTP call.
        # However, network calls are intentionally kept minimal here. If you prefer, swap to official SDK.
        import requests

        url = "https://api.openai.com/v1/responses"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {
            "model": model,
            "input": prompt,
            "max_output_tokens": 800,
        }

        resp = requests.post(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Extract text from the response in a robust way
        text = None
        # Responses API may contain outputs in different places; try common locations
        if "output" in data and isinstance(data["output"], list) and data["output"]:
            # Some Responses API variants put content under 'content' or 'text' keys inside items
            parts = []
            for x in data["output"]:
                if isinstance(x, dict):
                    val = x.get("content") or x.get("text") or ""
                    # If content is a list (common in Responses API), normalize it to a string
                    if isinstance(val, list):
                        subparts = []
                        for elem in val:
                            if isinstance(elem, dict):
                                subparts.append(elem.get("content") or elem.get("text") or json.dumps(elem))
                            else:
                                subparts.append(str(elem))
                        parts.append("\n".join([s for s in subparts if s]))
                    else:
                        parts.append(str(val))
                else:
                    parts.append(str(x))
            text = "\n".join([p for p in parts if p])
        elif "choices" in data and data["choices"]:
            first = data["choices"][0]
            if isinstance(first, dict):
                text = (first.get("message", {}) or {}).get("content") or first.get("text")
            else:
                text = str(first)
        else:
            text = json.dumps(data)

        # Try parsing JSON; if it fails, attempt to extract a JSON substring before retrying with a repair instruction
        parsed = None
        try:
            parsed = json.loads(text)
        except Exception:
            # If the response looks like a Python repr (list/dict with single quotes), try ast.literal_eval
            try:
                pyobj = ast.literal_eval(text)
                candidates = []
                if isinstance(pyobj, (list, tuple)):
                    for it in pyobj:
                        if isinstance(it, dict):
                            if 'text' in it and isinstance(it['text'], str):
                                candidates.append(it['text'])
                            if 'content' in it and isinstance(it['content'], str):
                                candidates.append(it['content'])
                elif isinstance(pyobj, dict):
                    if 'text' in pyobj and isinstance(pyobj['text'], str):
                        candidates.append(pyobj['text'])
                    if 'content' in pyobj and isinstance(pyobj['content'], str):
                        candidates.append(pyobj['content'])

                for cand in candidates:
                    # cand may be a JSON string; try to load it directly
                    try:
                        parsed = json.loads(cand)
                        break
                    except Exception:
                        # try extracting JSON substring from candidate
                        frag = self._extract_json_substring(cand)
                        if frag:
                            try:
                                parsed = json.loads(frag)
                                break
                            except Exception:
                                pass
            except Exception:
                # Not a Python literal; fall back to substring heuristics below
                pass

            if parsed is None:
                # Attempt to find a JSON object inside the returned text
                json_fragment = self._extract_json_substring(text)
                if json_fragment:
                    try:
                        parsed = json.loads(json_fragment)
                    except Exception:
                        parsed = None

        if parsed is None:
            # Retry with a repair instruction appended
            repair_prompt = prompt + "\n\nIf your previous response was not valid JSON, please output only the corrected JSON object now."
            body["input"] = repair_prompt
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            resp.raise_for_status()
            data2 = resp.json()
            text2 = None
            if "output" in data2 and isinstance(data2["output"], list) and data2["output"]:
                parts = []
                for x in data2["output"]:
                    if isinstance(x, dict):
                        parts.append(x.get("content") or x.get("text") or "")
                    else:
                        parts.append(str(x))
                text2 = "\n".join([p for p in parts if p])
            elif "choices" in data2 and data2["choices"]:
                first = data2["choices"][0]
                if isinstance(first, dict):
                    text2 = (first.get("message", {}) or {}).get("content") or first.get("text")
                else:
                    text2 = str(first)
            else:
                text2 = json.dumps(data2)

            # Try JSON substring extraction on the repair response as well
            try:
                parsed = json.loads(text2)
            except Exception:
                json_fragment2 = self._extract_json_substring(text2)
                if json_fragment2:
                    try:
                        parsed = json.loads(json_fragment2)
                    except Exception as exc:
                        parsed = {
                            "executive_summary": "",
                            "key_insights": [],
                            "suggested_charts": [],
                            "analysis_notes": "",
                            "limitations": f"LLM JSON parse error: {exc}; raw response included",
                            "raw_response": text2,
                        }
                else:
                    parsed = {
                        "executive_summary": "",
                        "key_insights": [],
                        "suggested_charts": [],
                        "analysis_notes": "",
                        "limitations": "LLM JSON parse error: response could not be parsed and no JSON fragment found; raw response included",
                        "raw_response": text2,
                    }

        # Very rough token & cost estimate
        token_estimate = int(len(prompt) / 4 + 800)
        cost_estimate = round(token_estimate * 0.000001, 6)

        return parsed, token_estimate, cost_estimate
