import json
from datetime import datetime
from pathlib import Path

from flask import jsonify, request, send_from_directory

from backend import artifacts
from backend import config
from backend import editorial_input
from backend import pipeline_flow
from backend.api.blueprint import api_bp
from backend.api.helpers import load_manifest, reject_client, reject_run_id
from backend.pipelines import get_pipeline, resolve_pipeline_id


@api_bp.get("/clients/<client_id>/runs")
def list_runs(client_id: str):
    runs_root = Path(config.CLIENTS_DIR) / client_id / "runs"
    if not runs_root.is_dir():
        return jsonify(runs=[])

    rows: list[dict] = []
    for p in sorted(
        runs_root.iterdir(),
        key=lambda x: x.name,
        reverse=True,
    ):
        if not p.is_dir():
            continue
        run_id = p.name
        manifest_path = p / "run_manifest.json"
        if manifest_path.is_file():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                manual = data.get("manual_inputs")
                row = {
                    "run_id": run_id,
                    "topic": data.get("topic") or "untitled",
                    "statuses": data.get("statuses") or {},
                    "timestamp": data.get("timestamp") or "",
                    "archived": bool(data.get("archived")),
                    "pipeline_id": resolve_pipeline_id(data),
                }
                if isinstance(manual, dict):
                    row["manual_inputs"] = {
                        k: manual[k]
                        for k in ("paragraph", "additional_details")
                        if manual.get(k)
                    }
                rows.append(row)
            except json.JSONDecodeError:
                rows.append(
                    {
                        "run_id": run_id,
                        "topic": "untitled",
                        "statuses": {},
                        "timestamp": "",
                        "archived": False,
                        "pipeline_id": "article",
                    }
                )
        else:
            rows.append(
                {
                    "run_id": run_id,
                    "topic": "untitled",
                    "statuses": {},
                    "timestamp": "",
                    "archived": False,
                    "pipeline_id": "article",
                }
            )

    return jsonify(runs=rows)


@api_bp.post("/clients/<client_id>/runs")
def create_run(client_id: str):
    body = request.get_json(silent=True) or {}
    pipeline_id = str(body.get("pipeline_id") or "article").strip() or "article"
    if pipeline_id not in ("article", "social_media"):
        return jsonify(detail="pipeline_id must be 'article' or 'social_media'"), 400

    context_summary: str | None = None
    if pipeline_id == "social_media":
        from backend import social_input
        from backend.context_summary import generate_context_summary

        manual = social_input.sanitize_social_manual_inputs(body.get("manual_inputs"))
        topic = (body.get("topic") or "").strip()
        if manual:
            built = social_input.topic_from_social(manual)
            if built:
                topic = built
        if not topic:
            return jsonify(
                detail="Post idea is required (describe your idea in the paragraph field)"
            ), 400
        display_topic = topic
        context_summary = generate_context_summary(client_id)
        wc_target = None
    else:
        manual = editorial_input.sanitize_manual_inputs(body.get("manual_inputs"))
        semrush = (body.get("semrush_notes") or "").strip()
        if isinstance(body.get("manual_inputs"), dict):
            semrush = semrush or str(body["manual_inputs"].get("semrush_notes") or "").strip()

        topic = (body.get("topic") or "").strip()
        if manual:
            built = editorial_input.build_topic_payload(manual, semrush_notes=semrush)
            if built:
                topic = built
            if not topic:
                topic = editorial_input.topic_title_from_fields(manual) or topic
        if not topic:
            return jsonify(detail="Topic is required (fill in the article form)"), 400

        display_topic = editorial_input.topic_title_from_fields(manual) or topic.split("\n", 1)[0][:500]
        wc_target = editorial_input.word_count_from_manual(manual)

    base = Path(config.CLIENTS_DIR) / client_id
    (base / "context").mkdir(parents=True, exist_ok=True)
    (base / "runs").mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pipeline = get_pipeline(pipeline_id)
    statuses = {name: "pending" for name in pipeline.step_order}
    artifacts.save_run_manifest(
        client_id,
        run_id,
        display_topic,
        statuses,
        pipeline_id=pipeline_id,
        manual_inputs=manual,
        target_word_count=wc_target,
        context_summary=context_summary,
    )

    logo_b64 = body.get("logo_base64")
    logo_name = str(body.get("logo_filename") or "").strip()
    if logo_b64:
        try:
            stored = artifacts.save_run_logo_from_base64(
                client_id, run_id, str(logo_b64), logo_name
            )
            artifacts.set_run_logo_file(client_id, run_id, stored)
        except ValueError as e:
            return jsonify(detail=str(e)), 400

    return jsonify(
        run_id=run_id,
        client_id=client_id,
        topic=display_topic,
        pipeline_id=pipeline_id,
    )


def _cancel_pipeline_step(client_id: str, run_id: str, step_name: str):
    """Reset a step stuck in ``running`` or ``error`` back to ``pending``."""
    manifest = load_manifest(client_id, run_id)
    pipeline_id = resolve_pipeline_id(manifest) if manifest else "article"
    pipeline = get_pipeline(pipeline_id)
    if step_name not in pipeline.step_order:
        return jsonify(detail=f"Unknown step_name: {step_name!r}"), 400

    if not manifest:
        return jsonify(detail="run not found"), 404
    topic = manifest.get("topic") or ""
    statuses = dict(manifest.get("statuses") or {})
    for name in pipeline.step_order:
        statuses.setdefault(name, "pending")

    st = statuses.get(step_name, "pending")
    if st not in ("running", "error"):
        return jsonify(detail="Step is not running or in error"), 400

    statuses[step_name] = "pending"
    manifest = load_manifest(client_id, run_id) or {}
    timings = dict(manifest.get("step_timings") or {})
    timings.pop(step_name, None)
    artifacts.save_run_manifest(
        client_id, run_id, topic, statuses, step_timings=timings
    )
    return jsonify(cancelled=True, step_name=step_name)


@api_bp.patch("/clients/<client_id>/runs/<run_id>")
def patch_run(client_id: str, run_id: str):
    """Body: ``{"action": "archive"|"unarchive"|"delete"|"cancel_step", "step_name": "..."}``."""
    bad = reject_client(client_id)
    if bad:
        return bad
    bad_run = reject_run_id(run_id)
    if bad_run:
        return bad_run

    body = request.get_json(silent=True) or {}
    action = (body.get("action") or "").strip().lower()

    if action == "archive":
        if not artifacts.set_run_archived(client_id, run_id, archived=True):
            return jsonify(detail="run not found"), 404
        return jsonify(archived=True, run_id=run_id)
    if action == "unarchive":
        if not artifacts.set_run_archived(client_id, run_id, archived=False):
            return jsonify(detail="run not found"), 404
        return jsonify(archived=False, run_id=run_id)
    if action == "delete":
        if not artifacts.delete_run(client_id, run_id):
            return jsonify(detail="run not found"), 404
        return jsonify(deleted=True, run_id=run_id)
    if action == "cancel_step":
        step_name = (body.get("step_name") or "").strip()
        if not step_name:
            return jsonify(detail="step_name is required for cancel_step"), 400
        return _cancel_pipeline_step(client_id, run_id, step_name)

    if action == "update_manual_inputs":
        manifest = load_manifest(client_id, run_id)
        if not manifest:
            return jsonify(detail="run not found"), 404
        if resolve_pipeline_id(manifest) != "social_media":
            return jsonify(
                detail="manual_inputs can only be edited on social_media runs",
            ), 400
        from backend import social_input

        manual = social_input.sanitize_social_manual_inputs(body.get("manual_inputs"))
        if not manual or not (manual.get("paragraph") or "").strip():
            return jsonify(detail="Post idea (paragraph) is required"), 400
        topic = social_input.topic_from_social(manual)
        if not topic:
            return jsonify(detail="Post idea (paragraph) is required"), 400
        statuses = manifest.get("statuses") or {}
        artifacts.save_run_manifest(
            client_id,
            run_id,
            topic,
            statuses,
            pipeline_id="social_media",
            manual_inputs=manual,
            step_timings=manifest.get("step_timings"),
            context_summary=manifest.get("context_summary"),
        )
        return jsonify(
            run_id=run_id,
            topic=topic,
            manual_inputs=manual,
        )

    return jsonify(
        detail="action must be archive, unarchive, delete, cancel_step, or update_manual_inputs",
    ), 400


@api_bp.post("/clients/<client_id>/runs/<run_id>/archive")
def archive_run(client_id: str, run_id: str):
    bad = reject_client(client_id)
    if bad:
        return bad
    bad_run = reject_run_id(run_id)
    if bad_run:
        return bad_run
    if not artifacts.set_run_archived(client_id, run_id, archived=True):
        return jsonify(detail="run not found"), 404
    return jsonify(archived=True, run_id=run_id)


@api_bp.post("/clients/<client_id>/runs/<run_id>/unarchive")
def unarchive_run(client_id: str, run_id: str):
    bad = reject_client(client_id)
    if bad:
        return bad
    bad_run = reject_run_id(run_id)
    if bad_run:
        return bad_run
    if not artifacts.set_run_archived(client_id, run_id, archived=False):
        return jsonify(detail="run not found"), 404
    return jsonify(archived=False, run_id=run_id)


@api_bp.delete("/clients/<client_id>/runs/<run_id>")
def delete_run(client_id: str, run_id: str):
    bad = reject_client(client_id)
    if bad:
        return bad
    bad_run = reject_run_id(run_id)
    if bad_run:
        return bad_run
    if not artifacts.delete_run(client_id, run_id):
        return jsonify(detail="run not found"), 404
    return jsonify(deleted=True, run_id=run_id)


@api_bp.get("/clients/<client_id>/runs/<run_id>")
def get_run(client_id: str, run_id: str):
    bad = reject_client(client_id)
    if bad:
        return bad
    bad_run = reject_run_id(run_id)
    if bad_run:
        return bad_run
    run_dir = Path(config.CLIENTS_DIR) / client_id / "runs" / run_id
    if not run_dir.is_dir():
        return jsonify(detail="run not found"), 404
    data = load_manifest(client_id, run_id)
    display_timings = artifacts.step_timings_for_display(client_id, run_id, data)
    if display_timings and not data.get("step_timings"):
        artifacts.save_run_manifest(
            client_id,
            run_id,
            data.get("topic") or "untitled",
            data.get("statuses") or {},
            step_timings=display_timings,
        )
    wc = data.get("target_word_count")
    if wc is None and isinstance(data.get("manual_inputs"), dict):
        from backend import editorial_input

        wc = editorial_input.word_count_from_manual(data.get("manual_inputs"))

    return jsonify(
        run_id=run_id,
        client_id=client_id,
        pipeline_id=resolve_pipeline_id(data),
        topic=data.get("topic") or "untitled",
        statuses=data.get("statuses") or {},
        timestamp=data.get("timestamp") or "",
        manual_inputs=data.get("manual_inputs"),
        target_word_count=wc,
        logo_file=data.get("logo_file"),
        step_timings=display_timings,
    )


@api_bp.get("/clients/<client_id>/runs/<run_id>/logo")
def get_run_logo(client_id: str, run_id: str):
    bad = reject_client(client_id)
    if bad:
        return bad
    bad_run = reject_run_id(run_id)
    if bad_run:
        return bad_run
    data = load_manifest(client_id, run_id)
    logo_file = data.get("logo_file") if data else None
    if not isinstance(logo_file, str) or not logo_file.strip():
        return jsonify(detail="no logo"), 404
    logo_file = logo_file.strip()
    if ".." in logo_file or "/" in logo_file or "\\" in logo_file:
        return jsonify(detail="invalid logo path"), 400
    run_dir = Path(config.CLIENTS_DIR) / client_id / "runs" / run_id
    path = run_dir / logo_file
    if not path.is_file():
        return jsonify(detail="logo not found"), 404
    return send_from_directory(run_dir, logo_file)


@api_bp.post("/clients/<client_id>/runs/<run_id>/steps/<step_name>")
def run_single_step(client_id: str, run_id: str, step_name: str):
    bad = reject_client(client_id)
    if bad:
        return bad
    bad_run = reject_run_id(run_id)
    if bad_run:
        return bad_run
    body = request.get_json(silent=True) or {}
    previous_artifact = (body.get("previous_artifact") or "").strip()

    manifest = load_manifest(client_id, run_id)
    pipeline_id = resolve_pipeline_id(manifest) if manifest else "article"
    try:
        pipeline = get_pipeline(pipeline_id)
    except ValueError as e:
        return jsonify(detail=str(e)), 400

    runner_fn = pipeline.step_runners.get(step_name)
    if runner_fn is None:
        return jsonify(detail=f"Unknown step_name: {step_name!r}"), 400

    topic = manifest.get("topic") or ""
    if pipeline.pipeline_id == "article" and step_name == "topic_card":
        manual = manifest.get("manual_inputs")
        if isinstance(manual, dict):
            built = editorial_input.build_topic_payload(manual)
            if built:
                previous_artifact = built
        if not previous_artifact:
            previous_artifact = topic
    statuses = dict(manifest.get("statuses") or {})
    for name in pipeline.step_order:
        statuses.setdefault(name, "pending")

    timings = artifacts.record_step_started(client_id, run_id, step_name)
    statuses[step_name] = "running"
    artifacts.save_run_manifest(
        client_id, run_id, topic, statuses, step_timings=timings
    )

    try:
        output = runner_fn(client_id, run_id, previous_artifact)
    except Exception as e:
        statuses[step_name] = "error"
        timings = artifacts.record_step_finished(
            client_id, run_id, step_name, "error"
        )
        artifacts.save_run_manifest(
            client_id, run_id, topic, statuses, step_timings=timings
        )
        return jsonify(detail=f"{type(e).__name__}: {e}"), 500

    statuses[step_name] = "done"
    timings = artifacts.record_step_finished(client_id, run_id, step_name, "done")
    artifacts.save_run_manifest(
        client_id, run_id, topic, statuses, step_timings=timings
    )
    return jsonify(output=output, step_name=step_name)


@api_bp.post("/clients/<client_id>/runs/<run_id>/final-output/repair")
def repair_final_output(client_id: str, run_id: str):
    """Repair final_output: FAQ, external links, optional full trim (query ?full=1)."""
    bad = reject_client(client_id)
    if bad:
        return bad
    bad_run = reject_run_id(run_id)
    if bad_run:
        return bad_run
    from backend import final_output_enforce

    try:
        text = artifacts.load_artifact(client_id, run_id, "final_output")
    except FileNotFoundError:
        return jsonify(error="final_output artifact not found"), 404
    full = request.args.get("full", "").lower() in ("1", "true", "yes")
    repaired = final_output_enforce.enforce_final_output(
        text, client_id, run_id, allow_llm_repair=full
    )
    if repaired != text:
        artifacts.save_artifact(client_id, run_id, "final_output", repaired)
    return jsonify(content=repaired)


@api_bp.post("/clients/<client_id>/runs/<run_id>/steps/<step_name>/cancel")
def cancel_step(client_id: str, run_id: str, step_name: str):
    bad = reject_client(client_id)
    if bad:
        return bad
    bad_run = reject_run_id(run_id)
    if bad_run:
        return bad_run
    return _cancel_pipeline_step(client_id, run_id, step_name)
