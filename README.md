# AI Data-to-Insights Generator 🎯

A small, production-quality portfolio project that converts CSV datasets into structured insights using a large language model.

Business value
--------------
- ⚡ Accelerates data exploration for analysts and stakeholders.
- 🧭 Produces concise, structured executive summaries and recommended visualizations.
- 👥 Encourages human review; AI outputs are suggestions, not final decisions.

How it works
------------
1. 🗄️ Load CSV with pandas (schema, sample rows, and summary stats are extracted).
2. 🤖 Send a compact, redacted summary to an LLM asking for structured insights.
3. 📦 Receive a strict JSON object with an executive summary, key insights, suggested charts, analysis notes, and limitations.
4. 💾 Save results to `output/insights.json` and append an entry to `output/run_log.json`.

Human-in-the-loop design
------------------------
- 🔒 The tool never executes AI-generated code.
- ✅ All LLM outputs are required to be valid JSON and are validated against a schema.
- ✋ Analysts must review suggestions, visualizations, and generated code before any action.

CLI
---
Example:

python data_insights.py \
  --input sample_data/sample_sales.csv \
  --question "Why did revenue drop in Q3?" \
  --model gpt-4o-mini \
  --out output

Dry run
-------
Use `--dry-run` to avoid API calls and produce deterministic fake outputs.

AI tool disclosure
------------------
Developed using GitHub Copilot and ChatGPT as productivity tools.

Screenshots
-----------
input
<img width="345" height="337" alt="image" src="https://github.com/user-attachments/assets/c7bd5268-971f-4068-995a-637fb1507fb7" />

output
<img width="1725" height="742" alt="image" src="https://github.com/user-attachments/assets/1f1eba7d-f786-4448-81d1-5c1b3c5d6e92" />

License
-------
MIT
