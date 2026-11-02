from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .artifacts import (
    audit_payload,
    preserve_human_audit,
    read_jsonl,
    render_comparison_markdown,
    render_html,
    write_json,
)
from .datasets import load_suites, validate_bundles
from .presets import PRESETS
from .runner import compare_runs, run_evaluation


def _private_evaluations_root() -> Path:
    mounted = Path("/data/private")
    if mounted.exists():
        return mounted / "evaluations"
    return Path(__file__).resolve().parents[5] / "data" / "private" / "evaluations"


def add_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = parent.add_parser("evaluate", help="executa e consolida avaliação HTTP do agente")
    commands = parser.add_subparsers(dest="evaluation_command", required=True)
    validate = commands.add_parser("validate-datasets")
    validate.add_argument("--suites", default="all")
    validate.add_argument("--archive")
    run = commands.add_parser("run")
    run.add_argument("--url", default="http://127.0.0.1:8000")
    run.add_argument("--preset", required=True, choices=sorted(PRESETS))
    run.add_argument("--suites", default="all")
    run.add_argument("--archive")
    run.add_argument("--assistant-profile")
    run.add_argument("--memory-profile", default="recent-window-v1")
    run.add_argument("--timeout", type=float, default=240)
    run.add_argument("--output")
    run.add_argument("--resume", action="store_true")
    compare = commands.add_parser("compare")
    compare.add_argument("--runs", nargs="+", required=True)
    compare.add_argument("--output")
    audit = commands.add_parser("audit")
    audit.add_argument("--run", required=True)
    return parser


def execute(args) -> None:
    names = [item.strip() for item in getattr(args, "suites", "all").split(",") if item.strip()]
    if args.evaluation_command == "validate-datasets":
        bundles = load_suites(names, args.archive)
        validate_bundles(bundles)
        print(json.dumps([{"suite": item.suite, "review_status": item.review_status,
                            "episodes": len(item.episodes), "runnable": item.runnable,
                            "reason": item.block_reason, "sha256": item.sha256}
                           for item in bundles], ensure_ascii=False, indent=2))
        return
    if args.evaluation_command == "run":
        output = Path(args.output) if args.output else (
            _private_evaluations_root() /
            f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{args.preset}"
        )
        result = run_evaluation(args.url, args.preset, names, output, args.archive,
                                args.assistant_profile, args.memory_profile,
                                args.timeout, args.resume)
        print(json.dumps({"output": result["output"], "records": result["manifest"]["records"],
                          "blocked": result["report"]["blocked_suites"]}, ensure_ascii=False, indent=2))
        return
    if args.evaluation_command == "compare":
        result = compare_runs([Path(item) for item in args.runs])
        output = Path(args.output) if args.output else Path("comparison.json")
        write_json(output, result)
        markdown_path = output.with_suffix(".md")
        markdown_path.write_text(render_comparison_markdown(result), encoding="utf-8")
        print(f"Comparação gravada em {output} e {markdown_path}")
        return
    run = Path(args.run)
    records = [item for item in read_jsonl(run / "records.jsonl")
               if item.get("schema_version") == "evaluation-turn-record.v1"]
    audit = audit_payload(records)
    audit_path = run / "audit.json"
    if audit_path.exists():
        try:
            audit = preserve_human_audit(
                audit, json.loads(audit_path.read_text(encoding="utf-8"))
            )
        except (OSError, json.JSONDecodeError):
            # A malformed editable file should not prevent a reviewer from
            # regenerating a clean audit package from immutable turn records.
            pass
    write_json(audit_path, audit)
    (run / "audit.html").write_text(render_html(audit, f"Auditoria — {run.name}"), encoding="utf-8")
    print(f"Auditoria atualizada em {run / 'audit.html'}")
