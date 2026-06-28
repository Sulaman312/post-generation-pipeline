"""Pipeline system prompts loaded from Markdown files (`steps/`).

Edit the `.md` files to change wording; imports stay stable:

    from backend import prompts
    prompts.STEP_3_PROMPT
"""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent / "steps"


def _load_md(filename: str) -> str:
    text = (_PROMPTS_DIR / filename).read_text(encoding="utf-8")
    if text.endswith("\n"):
        return text
    return text + "\n"


STEP_1_PROMPT = _load_md("01_topic_card.md")
STEP_2_PROMPT = _load_md("02_assignment_brief.md")
STEP_3_PROMPT = _load_md("03_research.md")
STEP_4_PROMPT = _load_md("04_outline.md")
STEP_5_PROMPT = _load_md("05_draft.md")
STEP_6_PROMPT = _load_md("06_fact_check.md")
STEP_7_PROMPT = _load_md("07_final_output.md")

# Semantic aliases. The numeric STEP_* constants follow the on-disk markdown filenames
# and intentionally do NOT include the `serp_research` pipeline step.
TOPIC_CARD_PROMPT = STEP_1_PROMPT
ASSIGNMENT_BRIEF_PROMPT = STEP_2_PROMPT
RESEARCH_PROMPT = STEP_3_PROMPT
OUTLINE_PROMPT = STEP_4_PROMPT
DRAFT_PROMPT = STEP_5_PROMPT
FACT_CHECK_PROMPT = STEP_6_PROMPT
FINAL_OUTPUT_PROMPT = STEP_7_PROMPT

__all__ = [
    "STEP_1_PROMPT",
    "STEP_2_PROMPT",
    "STEP_3_PROMPT",
    "STEP_4_PROMPT",
    "STEP_5_PROMPT",
    "STEP_6_PROMPT",
    "STEP_7_PROMPT",
    "TOPIC_CARD_PROMPT",
    "ASSIGNMENT_BRIEF_PROMPT",
    "RESEARCH_PROMPT",
    "OUTLINE_PROMPT",
    "DRAFT_PROMPT",
    "FACT_CHECK_PROMPT",
    "FINAL_OUTPUT_PROMPT",
]
