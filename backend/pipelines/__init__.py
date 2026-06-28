"""Pipeline registry (article + social media).

Keep the existing article pipeline intact (`backend/pipeline.py`), and add new pipelines
as separate modules to avoid accidental cross-coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


RunnerFn = Callable[[str, str, str], str]

# Keys that only exist on the social pipeline (used to infer pipeline_id on older runs).
_SOCIAL_STEP_KEYS = frozenset(
    {
        "client_profile_topic",
        "content_angle_intent",
        "image_prompt",
        "image_generation",
        "image_formats",
        "image_template",
        "captions",
        "review_checklist",
    }
)
_LEGACY_SOCIAL_STEP_KEYS = frozenset({"schedule_publish"})


@dataclass(frozen=True)
class PipelineSpec:
    pipeline_id: str
    step_order: list[str]
    step_runners: dict[str, RunnerFn]


def resolve_pipeline_id(manifest: dict | None) -> str:
    """Return the pipeline id for a run manifest, inferring social runs when needed."""
    if not isinstance(manifest, dict):
        return "article"
    pid = str(manifest.get("pipeline_id") or "").strip()
    statuses = manifest.get("statuses") or {}
    keys = set(statuses.keys()) if isinstance(statuses, dict) else set()
    if pid == "social_media":
        return "social_media"
    if keys & _SOCIAL_STEP_KEYS:
        return "social_media"
    if pid == "article" or not pid:
        return "article"
    return pid


def upgrade_manifest(manifest: dict) -> tuple[dict, bool]:
    """Normalize pipeline_id and step statuses for older social runs."""
    if not isinstance(manifest, dict):
        return manifest, False

    out = dict(manifest)
    resolved_pid = resolve_pipeline_id(out)
    changed = resolved_pid != (out.get("pipeline_id") or "article")
    out["pipeline_id"] = resolved_pid

    if resolved_pid != "social_media":
        return out, changed

    pipeline = get_pipeline("social_media")
    statuses = dict(out.get("statuses") or {})
    for legacy in _LEGACY_SOCIAL_STEP_KEYS:
        if legacy in statuses:
            statuses.pop(legacy, None)
            changed = True

    for name in pipeline.step_order:
        if name not in statuses:
            statuses[name] = "pending"
            changed = True

    ordered = {name: statuses[name] for name in pipeline.step_order}
    if ordered != out.get("statuses"):
        out["statuses"] = ordered
        changed = True

    return out, changed


def get_pipeline(pipeline_id: str) -> PipelineSpec:
    pid = (pipeline_id or "").strip() or "article"
    if pid == "article":
        from backend.pipeline import STEP_ORDER, STEP_RUNNERS

        return PipelineSpec(pipeline_id="article", step_order=list(STEP_ORDER), step_runners=STEP_RUNNERS)
    if pid == "social_media":
        from backend.social_pipeline import STEP_ORDER, STEP_RUNNERS

        return PipelineSpec(
            pipeline_id="social_media",
            step_order=list(STEP_ORDER),
            step_runners=STEP_RUNNERS,
        )
    raise ValueError(f"Unknown pipeline_id: {pid!r}")

