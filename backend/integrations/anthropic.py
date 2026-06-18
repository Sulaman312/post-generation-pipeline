"""Anthropic Claude API — editorial pipeline LLM steps.

Environment (see repo `env.example`):
  ANTHROPIC_API_KEY — required for all Claude-powered steps
  CLAUDE_MODEL       — default `claude-sonnet-4-20250514`
  MAX_TOKENS         — max output tokens per step (config.py)
  TEMPERATURE        — sampling temperature (config.py)

Docs: https://docs.anthropic.com/en/api/messages
"""

from __future__ import annotations

import logging
import time

from .. import config

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to `.env` (see env.example)."
            )
        try:
            import anthropic
        except ImportError as e:
            raise RuntimeError(
                "anthropic package not installed. Run: pip install anthropic"
            ) from e
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def chat_complete(
    system_msg: str,
    user_msg: str,
    *,
    step_label: str = "pipeline step",
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> str:
    """Call Claude with system + user messages; retry once after 3s on failure."""
    client = _get_client()
    model = config.CLAUDE_MODEL
    max_tok = max_tokens if max_tokens is not None else config.MAX_TOKENS
    temp = temperature if temperature is not None else config.TEMPERATURE

    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tok,
                temperature=temp,
                system=system_msg,
                messages=[{"role": "user", "content": user_msg}],
            )
            parts: list[str] = []
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    parts.append(block.text)
            raw = "".join(parts).strip()
            if not raw:
                raise ValueError("Claude returned empty content")
            return raw
        except Exception as e:
            last_exc = e
            logger.warning(
                "%s: Claude API attempt %s failed: %s",
                step_label,
                attempt + 1,
                e,
            )
            if attempt == 0:
                time.sleep(3)
            else:
                raise RuntimeError(
                    f"Claude API call failed after retry for {step_label}"
                ) from last_exc
    raise AssertionError("unreachable")
