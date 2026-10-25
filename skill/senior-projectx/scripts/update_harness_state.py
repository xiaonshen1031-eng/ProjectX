#!/usr/bin/env python3
"""Record feedback, preferences, regressions, and evaluations for the skill harness."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HARNESS = SKILL_ROOT / "harness"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")


def touch_state(harness: Path) -> dict[str, Any]:
    path = harness / "state" / "skill_state.json"
    state = load_json(
        path,
        {
            "schema_version": 1,
            "skill_version": "unknown",
            "last_modified": None,
            "last_regression": None,
            "preferences": {},
        },
    )
    state["last_modified"] = now_iso()
    atomic_write_json(path, state)
    return state


def record_feedback(args: argparse.Namespace, harness: Path) -> dict[str, Any]:
    event = {
        "timestamp": now_iso(),
        "classification": args.classification,
        "feedback": args.feedback,
        "interpretation": args.interpretation,
        "root_cause": args.root_cause,
        "status": args.status,
        "confidence": args.confidence,
        "evidence": args.evidence,
    }
    append_jsonl(harness / "feedback" / "user_feedback.jsonl", event)
    touch_state(harness)
    return event


def record_decision(args: argparse.Namespace, harness: Path) -> dict[str, Any]:
    event = {
        "timestamp": now_iso(),
        "decision": args.decision,
        "scope": args.scope,
        "rationale": args.rationale,
        "artifacts": args.artifact,
        "supersedes": args.supersedes,
    }
    append_jsonl(harness / "decisions" / "decision_log.jsonl", event)
    touch_state(harness)
    return event


def update_preference(args: argparse.Namespace, harness: Path) -> dict[str, Any]:
    path = harness / "state" / "skill_state.json"
    state = load_json(path, {"schema_version": 1, "skill_version": "unknown", "preferences": {}})
    preferences = state.setdefault("preferences", {})
    old = preferences.get(args.preference_id, {})
    old_count = int(old.get("evidence_count", 0))
    count = old_count + args.evidence_increment
    if args.confidence is None:
        old_confidence = float(old.get("confidence", 0.5))
        confidence = min(1.0, old_confidence + 0.1 * args.evidence_increment)
    else:
        confidence = args.confidence
    preference = {
        "statement": args.statement or old.get("statement", args.preference_id.replace("_", " ")),
        "scope": args.scope or old.get("scope", "all_manuscripts"),
        "confidence": round(confidence, 3),
        "evidence_count": count,
        "last_confirmed": now_iso()[:10],
        "status": args.status,
    }
    preferences[args.preference_id] = preference
    state["last_modified"] = now_iso()
    atomic_write_json(path, state)
    return preference


def register_regression(args: argparse.Namespace, harness: Path) -> dict[str, Any]:
    path = harness / "regression" / "regression_cases.json"
    registry = load_json(path, {"schema_version": 1, "cases": []})
    cases = registry.setdefault("cases", [])
    case = {
        "case_id": args.case_id,
        "task_type": args.task_type,
        "input_summary": args.input_summary,
        "expected_behavior": args.expected_behavior,
        "forbidden_behavior": args.forbidden_behavior,
        "relevant_rule": args.relevant_rule,
    }
    matches = [idx for idx, item in enumerate(cases) if item.get("case_id") == args.case_id]
    if matches and not args.replace:
        raise ValueError(f"Regression case already exists: {args.case_id}; pass --replace to update it.")
    if matches:
        cases[matches[0]] = case
    else:
        cases.append(case)
    atomic_write_json(path, registry)
    touch_state(harness)
    return case


def record_eval(args: argparse.Namespace, harness: Path) -> dict[str, Any]:
    path = harness / "evals" / "eval_registry.json"
    registry = load_json(path, {"schema_version": 1, "runs": []})
    runs = registry.setdefault("runs", [])
    run = {
        "eval_id": args.eval_id,
        "timestamp": now_iso(),
        "status": args.status,
        "checks": args.check,
        "artifacts": args.artifact,
        "notes": args.notes,
    }
    runs.append(run)
    atomic_write_json(path, registry)
    state_path = harness / "state" / "skill_state.json"
    state = load_json(state_path, {"schema_version": 1, "skill_version": "unknown", "preferences": {}})
    state["last_modified"] = now_iso()
    state["last_regression"] = {"eval_id": args.eval_id, "status": args.status, "timestamp": run["timestamp"]}
    atomic_write_json(state_path, state)
    return run


def record_version(args: argparse.Namespace, harness: Path) -> dict[str, Any]:
    path = harness / "state" / "skill_state.json"
    state = load_json(path, {"schema_version": 1, "skill_version": "unknown", "preferences": {}})
    previous = str(state.get("skill_version", "unknown"))
    timestamp = now_iso()
    history = state.setdefault("version_history", [])
    if any(item.get("version") == args.version for item in history if isinstance(item, dict)):
        raise ValueError(f"Version already recorded: {args.version}")
    event = {
        "version": args.version,
        "previous_version": previous,
        "timestamp": timestamp,
        "summary": args.summary,
    }
    history.append(event)
    state["skill_version"] = args.version
    state["last_modified"] = timestamp
    atomic_write_json(path, state)
    return event


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness-root", type=Path, default=DEFAULT_HARNESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    feedback = subparsers.add_parser("feedback", help="Append a classified feedback event.")
    feedback.add_argument("--classification", required=True, choices=["one_off", "project", "domain", "preference", "skill"])
    feedback.add_argument("--feedback", required=True)
    feedback.add_argument("--interpretation", required=True)
    feedback.add_argument("--root-cause", required=True)
    feedback.add_argument("--status", default="applied", choices=["observed", "applied", "promoted", "rejected", "deprecated"])
    feedback.add_argument("--confidence", type=float, default=1.0)
    feedback.add_argument("--evidence", action="append", default=[])

    decision = subparsers.add_parser("decision", help="Append a promotion or deprecation decision.")
    decision.add_argument("--decision", required=True)
    decision.add_argument("--scope", required=True, choices=["project", "domain", "preference", "skill"])
    decision.add_argument("--rationale", required=True)
    decision.add_argument("--artifact", action="append", default=[])
    decision.add_argument("--supersedes", action="append", default=[])

    preference = subparsers.add_parser("preference", help="Update preference confidence and evidence count.")
    preference.add_argument("--preference-id", required=True)
    preference.add_argument("--statement", default="")
    preference.add_argument("--scope", default="")
    preference.add_argument("--confidence", type=float)
    preference.add_argument("--evidence-increment", type=int, default=1)
    preference.add_argument("--status", default="active", choices=["active", "deprecated"])

    regression = subparsers.add_parser("regression", help="Register a stable behavioral regression case.")
    regression.add_argument("--case-id", required=True)
    regression.add_argument("--task-type", required=True)
    regression.add_argument("--input-summary", required=True)
    regression.add_argument("--expected-behavior", required=True)
    regression.add_argument("--forbidden-behavior", required=True)
    regression.add_argument("--relevant-rule", required=True)
    regression.add_argument("--replace", action="store_true")

    evaluation = subparsers.add_parser("eval", help="Append an evaluation result and update last_regression.")
    evaluation.add_argument("--eval-id", required=True)
    evaluation.add_argument("--status", required=True, choices=["pass", "fail", "partial"])
    evaluation.add_argument("--check", action="append", default=[])
    evaluation.add_argument("--artifact", action="append", default=[])
    evaluation.add_argument("--notes", default="")

    version = subparsers.add_parser("version", help="Record a skill-version transition in durable state.")
    version.add_argument("--version", required=True)
    version.add_argument("--summary", required=True)
    return parser


def main() -> None:
    # Emit portable JSON even when Windows defaults to a legacy console codepage.
    import sys
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = build_parser()
    args = parser.parse_args()
    harness = args.harness_root.resolve()
    handlers = {
        "feedback": record_feedback,
        "decision": record_decision,
        "preference": update_preference,
        "regression": register_regression,
        "eval": record_eval,
        "version": record_version,
    }
    try:
        result = handlers[args.command](args, harness)
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
