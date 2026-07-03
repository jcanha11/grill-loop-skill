#!/usr/bin/env python3
"""Deterministic state manager for the grill-loop skill."""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 2
ROUTES = {"FAST_PASS", "RESEARCH", "JUDGE", "ESCALATE"}
DECISIONS = {"ACCEPT", "REJECT", "CONSERVATIVE", "USER_REQUIRED"}
TERMINAL_STATUSES = {"passed", "conditional_pass", "stopped"}
DIMENSION_MAXIMA = {
    "objective_target": 15,
    "evidence_denominator": 20,
    "mechanism": 15,
    "measurement": 15,
    "execution": 15,
    "risks": 10,
    "clarity": 10,
}


class StateError(ValueError):
    pass


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def state_path(run_dir):
    return Path(run_dir).resolve() / "state.json"


def atomic_write_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_write_json(path, value):
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load_json(path):
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise StateError("File not found: {}".format(path)) from exc
    except json.JSONDecodeError as exc:
        raise StateError("Invalid JSON in {}: {}".format(path, exc)) from exc


def load_state(run_dir):
    path = state_path(run_dir)
    state = load_json(path)
    if state.get("schema_version") != SCHEMA_VERSION:
        raise StateError("Unsupported state schema version")
    return state, path


def require_string(packet, key):
    value = packet.get(key)
    if not isinstance(value, str) or not value.strip():
        raise StateError("{} must be a non-empty string".format(key))
    return value.strip()


def require_string_list(packet, key):
    value = packet.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise StateError("{} must be a list of strings".format(key))
    return value


def validate_packet(packet, mode):
    if not isinstance(packet, dict):
        raise StateError("Decision packet must be a JSON object")

    for key in ("question", "recommendation", "rationale", "impact"):
        require_string(packet, key)

    route = require_string(packet, "route")
    decision = require_string(packet, "decision")
    if route not in ROUTES:
        raise StateError("route must be one of {}".format(sorted(ROUTES)))
    if decision not in DECISIONS:
        raise StateError("decision must be one of {}".format(sorted(DECISIONS)))

    confidence = packet.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise StateError("confidence must be a number from 0 to 1")
    if confidence < 0 or confidence > 1:
        raise StateError("confidence must be a number from 0 to 1")

    score = packet.get("score")
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        raise StateError("score must be an integer from 0 to 100")

    dimensions = packet.get("dimension_scores")
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSION_MAXIMA):
        raise StateError("dimension_scores must contain exactly the rubric dimension keys")
    for key, maximum in DIMENSION_MAXIMA.items():
        value = dimensions[key]
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
            raise StateError("{} must be an integer from 0 to {}".format(key, maximum))
    if sum(dimensions.values()) != score:
        raise StateError("dimension_scores must sum to score")

    vetoes = require_string_list(packet, "vetoes")
    require_string_list(packet, "high_impact_open")
    if not isinstance(packet.get("material_new_issue"), bool):
        raise StateError("material_new_issue must be true or false")

    evidence = packet.get("evidence")
    if not isinstance(evidence, list):
        raise StateError("evidence must be a list")
    for item in evidence:
        if not isinstance(item, dict):
            raise StateError("each evidence item must be an object")
        require_string(item, "source")
        require_string(item, "fact")

    artifact_sha256 = require_string(packet, "artifact_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", artifact_sha256):
        raise StateError("artifact_sha256 must be 64 lowercase hexadecimal characters")

    if route == "FAST_PASS":
        if confidence < 0.90:
            raise StateError("FAST_PASS requires confidence >= 0.90")
        if vetoes:
            raise StateError("FAST_PASS cannot contain vetoes")
        if decision != "ACCEPT":
            raise StateError("FAST_PASS requires ACCEPT")

    if route == "ESCALATE":
        if mode == "supervised" and decision != "USER_REQUIRED":
            raise StateError("supervised ESCALATE requires USER_REQUIRED")
        if mode == "autonomous" and decision not in {"CONSERVATIVE", "USER_REQUIRED"}:
            raise StateError("autonomous ESCALATE requires CONSERVATIVE or USER_REQUIRED")
    elif decision == "USER_REQUIRED":
        raise StateError("USER_REQUIRED is only valid with ESCALATE")

    return packet


def render_decisions(state):
    lines = [
        "# Grill Loop Decisions",
        "",
        "- Run ID: `{}`".format(state["run_id"]),
        "- Mode: `{}`".format(state["mode"]),
        "- Status: `{}`".format(state["status"]),
        "- Current score: `{}`".format(state["current_score"]),
        "",
    ]
    if not state["decisions"]:
        lines.extend(["No decisions recorded.", ""])
        return "\n".join(lines)

    for item in state["decisions"]:
        lines.extend(
            [
                "## Iteration {}: {}".format(item["iteration"], item["route"]),
                "",
                "- Question: {}".format(item["question"]),
                "- Recommendation: {}".format(item["recommendation"]),
                "- Decision: `{}`".format(item["decision"]),
                "- Confidence: `{:.2f}`".format(item["confidence"]),
                "- Score: `{}`".format(item["score"]),
                "- Rationale: {}".format(item["rationale"]),
                "- Impact: {}".format(item["impact"]),
            ]
        )
        if item.get("snapshot"):
            lines.append("- Snapshot: `{}`".format(item["snapshot"]))
        if item["vetoes"]:
            lines.append("- Vetoes: {}".format("; ".join(item["vetoes"])))
        if item["high_impact_open"]:
            lines.append("- Open high-impact items: {}".format("; ".join(item["high_impact_open"])))
        if item["evidence"]:
            lines.append("- Evidence:")
            for evidence in item["evidence"]:
                lines.append("  - `{}` — {}".format(evidence["source"], evidence["fact"]))
        lines.append("")
    return "\n".join(lines)


def persist(state, path):
    state["updated_at"] = now_utc()
    atomic_write_json(path, state)
    atomic_write_text(path.parent / "decisions.md", render_decisions(state))


def public_summary(state):
    blocking = blocking_high_impact_items(state)
    return {
        "run_id": state["run_id"],
        "mode": state["mode"],
        "status": state["status"],
        "iteration": state["iteration"],
        "current_score": state["current_score"],
        "current_draft": state["current_draft"],
        "vetoes": state["vetoes"],
        "high_impact_open": state["high_impact_open"],
        "blocking_high_impact_open": blocking,
        "pending_escalations": sum(1 for item in state["escalations"] if item["status"] == "pending"),
        "stop_reason": state["stop_reason"],
    }


def command_init(args):
    source = Path(args.source).resolve()
    run_dir = Path(args.run_dir).resolve()
    path = state_path(run_dir)
    if not source.is_file():
        raise StateError("Source plan does not exist: {}".format(source))
    if path.exists():
        raise StateError("Run already exists at {}; resume it or choose another run directory".format(run_dir))

    drafts = run_dir / "drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    baseline = drafts / "000-baseline.md"
    shutil.copy2(str(source), str(baseline))
    created = now_utc()
    state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": str(uuid.uuid4()),
        "mode": args.mode,
        "status": "active",
        "source": str(source),
        "run_dir": str(run_dir),
        "created_at": created,
        "updated_at": created,
        "iteration": 0,
        "thresholds": {
            "score_target": args.score_target,
            "stable_iterations": args.stable_iterations,
            "stagnation_delta": args.stagnation_delta,
            "max_iterations": args.max_iterations,
        },
        "current_score": None,
        "dimension_scores": {},
        "current_draft": str(baseline.relative_to(run_dir)),
        "current_draft_sha256": sha256_file(baseline),
        "snapshots": [str(baseline.relative_to(run_dir))],
        "score_history": [],
        "vetoes": [],
        "high_impact_open": [],
        "escalations": [],
        "decisions": [],
        "stop_reason": None,
    }
    persist(state, path)
    print(json.dumps(public_summary(state), ensure_ascii=False, indent=2))


def copy_candidate(candidate, run_dir, iteration):
    candidate_path = Path(candidate).resolve()
    if not candidate_path.is_file():
        raise StateError("Candidate draft does not exist: {}".format(candidate_path))
    destination = run_dir / "drafts" / "{:03d}.md".format(iteration)
    shutil.copy2(str(candidate_path), str(destination))
    return str(destination.relative_to(run_dir))


def evaluate_stop(state):
    thresholds = state["thresholds"]
    history = state["score_history"]
    stable_count = thresholds["stable_iterations"]
    stable = (
        len(history) >= stable_count
        and all(not item["material_new_issue"] for item in history[-stable_count:])
    )
    blocking_high_impact = blocking_high_impact_items(state)
    quality_pass = (
        state["current_score"] >= thresholds["score_target"]
        and not state["vetoes"]
        and not blocking_high_impact
        and stable
    )
    if quality_pass:
        pending = any(item["status"] == "pending" for item in state["escalations"])
        state["status"] = "conditional_pass" if pending else "passed"
        state["stop_reason"] = "quality_threshold_met"
        return

    if len(history) >= 3:
        improvement = history[-1]["score"] - history[-3]["score"]
        if improvement < thresholds["stagnation_delta"]:
            state["status"] = "stopped"
            state["stop_reason"] = "stagnation"
            return

    if state["iteration"] >= thresholds["max_iterations"]:
        state["status"] = "stopped"
        state["stop_reason"] = "max_iterations"
        return

    state["status"] = "active"
    state["stop_reason"] = None


def blocking_high_impact_items(state):
    pending_items = set()
    for escalation in state.get("escalations", []):
        if escalation.get("status") == "pending":
            pending_items.update(escalation.get("items", []))
    return [item for item in state.get("high_impact_open", []) if item not in pending_items]


def command_record(args):
    state, path = load_state(args.run_dir)
    run_dir = path.parent
    if state["status"] in TERMINAL_STATUSES:
        raise StateError("Run is terminal with status {}".format(state["status"]))
    if state["status"] == "paused" and not args.resume:
        raise StateError("Run is paused; resolve the user question and pass --resume")
    if state["status"] == "active" and args.resume:
        raise StateError("--resume is only valid for a paused run")

    packet = validate_packet(load_json(args.input), state["mode"])
    if args.candidate and packet["decision"] not in {"ACCEPT", "CONSERVATIVE"}:
        raise StateError("Only ACCEPT or CONSERVATIVE can include a candidate draft")
    if args.candidate and packet["route"] == "FAST_PASS":
        raise StateError("FAST_PASS cannot include a candidate draft")
    if (
        args.candidate
        and packet["route"] != "FAST_PASS"
        and packet["decision"] in {"ACCEPT", "CONSERVATIVE"}
        and not packet["material_new_issue"]
    ):
        raise StateError("An accepted candidate on a non-FAST_PASS route must set material_new_issue=true")
    if packet["material_new_issue"] and packet["decision"] in {"ACCEPT", "CONSERVATIVE"} and not args.candidate:
        raise StateError("An accepted material change requires a candidate draft")

    retained_artifact = Path(args.candidate).resolve() if args.candidate else run_dir / state["current_draft"]
    if not retained_artifact.is_file():
        raise StateError("Scored artifact does not exist: {}".format(retained_artifact))
    actual_sha256 = sha256_file(retained_artifact)
    if packet["artifact_sha256"] != actual_sha256:
        raise StateError(
            "artifact_sha256 does not match the artifact retained by this decision; rescore the candidate"
        )

    iteration = state["iteration"] + 1
    snapshot = None
    if args.candidate:
        snapshot = copy_candidate(args.candidate, run_dir, iteration)

    if args.resume:
        pending = [item for item in state["escalations"] if item["status"] == "pending"]
        if not pending:
            raise StateError("No pending escalation exists to resume")
        pending[-1]["status"] = "resolved"
        pending[-1]["resolved_at"] = now_utc()
        pending[-1]["resolution"] = packet["rationale"]

    decision_record = dict(packet)
    decision_record.update(
        {
            "iteration": iteration,
            "recorded_at": now_utc(),
            "snapshot": snapshot,
        }
    )
    state["decisions"].append(decision_record)
    state["iteration"] = iteration
    state["current_score"] = packet["score"]
    state["dimension_scores"] = packet["dimension_scores"]
    state["vetoes"] = packet["vetoes"]
    state["high_impact_open"] = packet["high_impact_open"]
    state["score_history"].append(
        {
            "iteration": iteration,
            "score": packet["score"],
            "material_new_issue": packet["material_new_issue"],
        }
    )
    if snapshot:
        state["current_draft"] = snapshot
        state["current_draft_sha256"] = actual_sha256
        state["snapshots"].append(snapshot)

    if packet["route"] == "ESCALATE":
        escalation = {
            "iteration": iteration,
            "question": packet["question"],
            "decision": packet["decision"],
            "rationale": packet["rationale"],
            "items": packet["high_impact_open"],
            "status": "pending",
            "created_at": now_utc(),
        }
        state["escalations"].append(escalation)
        if state["mode"] == "supervised":
            state["status"] = "paused"
            state["stop_reason"] = "user_required"
        elif packet["decision"] == "USER_REQUIRED":
            state["status"] = "stopped"
            state["stop_reason"] = "no_safe_conservative_branch"
        else:
            evaluate_stop(state)
    else:
        evaluate_stop(state)

    persist(state, path)
    print(json.dumps(public_summary(state), ensure_ascii=False, indent=2))


def command_status(args):
    state, _ = load_state(args.run_dir)
    print(json.dumps(public_summary(state), ensure_ascii=False, indent=2))


def command_validate(args):
    state, path = load_state(args.run_dir)
    required = {
        "run_id",
        "mode",
        "status",
        "source",
        "iteration",
        "thresholds",
        "current_draft",
        "score_history",
        "decisions",
    }
    missing = required - set(state)
    if missing:
        raise StateError("State is missing keys: {}".format(sorted(missing)))
    draft = path.parent / state["current_draft"]
    if not draft.is_file():
        raise StateError("Current draft is missing: {}".format(draft))
    if state.get("current_draft_sha256") != sha256_file(draft):
        raise StateError("Current draft hash does not match state")
    print(json.dumps({"valid": True, **public_summary(state)}, ensure_ascii=False, indent=2))


def command_finalize(args):
    state, path = load_state(args.run_dir)
    if state["status"] not in TERMINAL_STATUSES:
        raise StateError("Cannot finalize a run with status {}".format(state["status"]))
    source = path.parent / state["current_draft"]
    final_path = path.parent / "final.md"
    shutil.copy2(str(source), str(final_path))
    state["finalized_at"] = now_utc()
    state["final_path"] = str(final_path.relative_to(path.parent))
    persist(state, path)
    result = public_summary(state)
    result["final_path"] = state["final_path"]
    result["decisions_path"] = "decisions.md"
    print(json.dumps(result, ensure_ascii=False, indent=2))


def command_abort(args):
    state, path = load_state(args.run_dir)
    if state["status"] in TERMINAL_STATUSES:
        raise StateError("Run is already terminal with status {}".format(state["status"]))
    state["status"] = "stopped"
    state["stop_reason"] = args.reason
    if args.detail:
        state["abort_detail"] = args.detail
    persist(state, path)
    print(json.dumps(public_summary(state), ensure_ascii=False, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize a grill-loop run")
    init_parser.add_argument("--source", required=True)
    init_parser.add_argument("--mode", choices=("supervised", "autonomous"), required=True)
    init_parser.add_argument("--run-dir", default=".grill-loop")
    init_parser.add_argument("--score-target", type=int, default=85)
    init_parser.add_argument("--stable-iterations", type=int, default=2)
    init_parser.add_argument("--stagnation-delta", type=int, default=3)
    init_parser.add_argument("--max-iterations", type=int, default=10)
    init_parser.set_defaults(func=command_init)

    record_parser = subparsers.add_parser("record", help="record one iteration")
    record_parser.add_argument("--run-dir", default=".grill-loop")
    record_parser.add_argument("--input", required=True)
    record_parser.add_argument("--candidate")
    record_parser.add_argument("--resume", action="store_true")
    record_parser.set_defaults(func=command_record)

    status_parser = subparsers.add_parser("status", help="show current run status")
    status_parser.add_argument("--run-dir", default=".grill-loop")
    status_parser.set_defaults(func=command_status)

    validate_parser = subparsers.add_parser("validate", help="validate current state")
    validate_parser.add_argument("--run-dir", default=".grill-loop")
    validate_parser.set_defaults(func=command_validate)

    finalize_parser = subparsers.add_parser("finalize", help="copy the best draft to final.md")
    finalize_parser.add_argument("--run-dir", default=".grill-loop")
    finalize_parser.set_defaults(func=command_finalize)

    abort_parser = subparsers.add_parser("abort", help="stop an active run for a controller-level failure")
    abort_parser.add_argument("--run-dir", default=".grill-loop")
    abort_parser.add_argument(
        "--reason",
        choices=("subagent_failure", "controller_failure", "user_cancelled"),
        required=True,
    )
    abort_parser.add_argument("--detail")
    abort_parser.set_defaults(func=command_abort)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", None) == "init":
        if not 0 <= args.score_target <= 100:
            parser.error("--score-target must be from 0 to 100")
        if args.stable_iterations < 1 or args.max_iterations < 1 or args.stagnation_delta < 0:
            parser.error("iteration and stagnation settings must be non-negative")
    try:
        args.func(args)
    except StateError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
