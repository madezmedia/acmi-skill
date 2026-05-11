#!/usr/bin/env python3
"""Programmatic grader for the ACMI skill evals. Walks each run, scores
assertions, writes grading.json per run + benchmark.json + benchmark.md."""

import json
import os
import re
import sys
import statistics
from pathlib import Path

WS = Path(sys.argv[1] if len(sys.argv) > 1 else "/sessions/lucid-awesome-hamilton/mnt/outputs/acmi-workspace/iteration-1")

# Real MCP tool param names (from loaded schemas)
VALID_EVENT_PARAMS = {"namespace", "id", "source", "summary", "kind", "correlationId"}
VALID_WORK_EVENT_PARAMS = {"id", "source", "summary", "sessionId"}
VALID_PROFILE_PARAMS = {"namespace", "id", "profile"}
VALID_SIGNAL_PARAMS = {"namespace", "id", "signals"}
VALID_BOOTSTRAP_PARAMS = {"agentId"}
VALID_ROLLUP_PARAMS = {"agentId", "rollup"}
INVENTED_PARAM_RED_FLAGS = {"workId", "eventType", "addressedTo", "addressed_to", "recipients", "to"}


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except Exception as e:
        return {"_load_error": str(e)}


def _walk_calls(result: dict) -> list[dict]:
    calls = result.get("tool_calls") or []
    if not isinstance(calls, list):
        return []
    return [c for c in calls if isinstance(c, dict)]


def _tool_name(call: dict) -> str:
    name = call.get("tool") or call.get("name") or ""
    # strip mcp__acmi__ prefix
    return name.split("__")[-1] if name else ""


def _tool_input(call: dict) -> dict:
    return call.get("input") or call.get("args") or call.get("arguments") or {}


def grade_eval_1(result: dict) -> list[dict]:
    """Bootstrap eval — agent should call acmi_spawn and acmi_bootstrap (or
    equivalent) and produce a prioritized brief that surfaces handoffs."""
    calls = _walk_calls(result)
    names = [_tool_name(c) for c in calls]
    out = []

    out.append({
        "text": "Calls acmi_bootstrap or acmi_get on the agent",
        "passed": "acmi_bootstrap" in names or any(
            n == "acmi_get" and _tool_input(c).get("namespace") == "agent"
            for n, c in zip(names, calls)
        ),
        "evidence": f"Called: {names}",
    })

    out.append({
        "text": "Calls acmi_spawn at session start",
        "passed": "acmi_spawn" in names,
        "evidence": f"Called: {names}",
    })

    out.append({
        "text": "Reads cross-thread context via acmi_cat",
        "passed": "acmi_cat" in names,
        "evidence": f"Called: {names}",
    })

    response = (result.get("user_response") or "").lower()
    out.append({
        "text": "User response surfaces handoffs explicitly",
        "passed": "handoff" in response or "delegation" in response,
        "evidence": "found 'handoff' or 'delegation' in response" if ("handoff" in response or "delegation" in response) else "neither term in response",
    })

    out.append({
        "text": "User response is prioritized (mentions priority order)",
        "passed": any(t in response for t in ["1.", "first", "priority", "p0", "p1", "top action", "next step"]),
        "evidence": "found priority signal" if any(t in response for t in ["1.", "first", "priority", "p0", "p1"]) else "no priority signal",
    })

    return out


def grade_eval_2(result: dict) -> list[dict]:
    """Milestone eval — must use acmi_event/acmi_work_event with real param
    names, fresh correlationId, summary convention, and document
    parentCorrelationId workaround."""
    calls = _walk_calls(result)
    out = []

    if not calls:
        return [{"text": "Has at least one tool call", "passed": False, "evidence": "no tool_calls"}]

    main = calls[0]
    name = _tool_name(main)
    inp = _tool_input(main)

    out.append({
        "text": "Uses acmi_work_event (work-item-aware) not raw acmi_event",
        "passed": name == "acmi_work_event",
        "evidence": f"called: {name}",
    })

    valid = VALID_WORK_EVENT_PARAMS if name == "acmi_work_event" else VALID_EVENT_PARAMS
    used = set(inp.keys())
    invented = used - valid
    out.append({
        "text": "Uses only real MCP parameter names (no invented like workId/eventType/addressedTo)",
        "passed": not (invented & INVENTED_PARAM_RED_FLAGS) and invented.issubset({"correlationId", "kind"} | valid),
        "evidence": f"params={sorted(used)}, valid={sorted(valid)}, red-flags-found={sorted(invented & INVENTED_PARAM_RED_FLAGS)}",
    })

    cid = inp.get("correlationId", "")
    parent_cid = "mikeyDeadlineDayDecisions-1778390495224"
    out.append({
        "text": "Generates a NEW correlationId, does not reuse the parent's",
        "passed": cid != parent_cid and cid != "",
        "evidence": f"correlationId={cid!r}, parent={parent_cid!r}",
    })

    out.append({
        "text": "correlationId follows <descCamel>-<msEpoch> form",
        "passed": bool(re.match(r"^[a-z][a-zA-Z0-9]*-\d{10,}$", cid)),
        "evidence": f"correlationId={cid!r}",
    })

    summary = inp.get("summary", "")
    out.append({
        "text": "Summary follows [kind-tag @recipient ...] convention",
        "passed": summary.startswith("[milestone-shipped") and "@bentley" in summary and "@mikey" in summary,
        "evidence": f"summary={summary[:120]!r}",
    })

    response_combined = (result.get("user_response", "") + result.get("reasoning", "")).lower()
    out.append({
        "text": "Documents the parentCorrelationId MCP-vs-SDK workaround",
        "passed": ("parent" in response_combined and ("workaround" in response_combined or "drift" in response_combined or "embed" in response_combined or "v1.3" in response_combined)) or "child-of" in summary.lower(),
        "evidence": "documented" if ("workaround" in response_combined or "child-of" in summary.lower()) else "not documented",
    })

    return out


def grade_eval_3(result: dict) -> list[dict]:
    """Rollup eval — must call acmi_rollup_set; rollup must have multiple
    cross-session keys beyond a single summary string."""
    calls = _walk_calls(result)
    names = [_tool_name(c) for c in calls]
    out = []

    out.append({
        "text": "Calls acmi_rollup_set",
        "passed": "acmi_rollup_set" in names,
        "evidence": f"called: {names}",
    })

    rollup_obj = result.get("rollup_object") or {}
    if not rollup_obj:
        # try to extract from tool call
        for c in calls:
            if _tool_name(c) == "acmi_rollup_set":
                raw = _tool_input(c).get("rollup")
                if isinstance(raw, str):
                    try:
                        rollup_obj = json.loads(raw)
                    except Exception:
                        pass
                elif isinstance(raw, dict):
                    rollup_obj = raw

    out.append({
        "text": "Rollup has session_summary key (or close synonym)",
        "passed": any(k in rollup_obj for k in ("session_summary", "summary", "session_recap", "narrative")),
        "evidence": f"keys={list(rollup_obj.keys())}",
    })

    out.append({
        "text": "Rollup captures open_blockers / pending_items",
        "passed": any(k in rollup_obj for k in ("open_blockers", "blockers", "pending", "open_items", "open_questions")),
        "evidence": f"keys={list(rollup_obj.keys())}",
    })

    out.append({
        "text": "Rollup defines next-session priorities",
        "passed": any(k in rollup_obj for k in ("next_session_priorities", "priorities", "next_actions", "first_action", "next_steps")),
        "evidence": f"keys={list(rollup_obj.keys())}",
    })

    # key_correlation_ids — preserves causal links for next session bootstrap
    serialized = json.dumps(rollup_obj)
    out.append({
        "text": "Rollup preserves key correlationIds for cross-session linking",
        "passed": "claudeEngineerSmitheryQualityWin-1778174324664" in serialized,
        "evidence": "cid preserved" if "claudeEngineerSmitheryQualityWin-1778174324664" in serialized else "cid missing",
    })

    out.append({
        "text": "Rollup is structured (multi-key) not just a paragraph",
        "passed": isinstance(rollup_obj, dict) and len(rollup_obj.keys()) >= 4,
        "evidence": f"key count={len(rollup_obj.keys()) if isinstance(rollup_obj, dict) else 'n/a'}",
    })

    return out


GRADERS = {
    "eval-1-fresh-session-bootstrap": grade_eval_1,
    "eval-2-log-milestone-with-chain": grade_eval_2,
    "eval-3-session-end-rollup": grade_eval_3,
}


def main() -> int:
    bench = {"skill_name": "acmi", "iteration": 1, "evals": []}
    for eval_dir in sorted(WS.iterdir()):
        if not eval_dir.is_dir() or not eval_dir.name.startswith("eval-"):
            continue
        grader = GRADERS.get(eval_dir.name)
        if not grader:
            continue
        eval_record = {"eval_id": eval_dir.name, "configs": {}}
        for config in ("with_skill", "without_skill"):
            cdir = eval_dir / config
            if not cdir.exists():
                continue
            result = _load(cdir / "outputs" / "result.json")
            timing = _load(cdir / "timing.json") or {}
            assertions = grader(result or {})
            grading = {"expectations": assertions}
            (cdir / "grading.json").write_text(json.dumps(grading, indent=2))
            passes = sum(1 for a in assertions if a.get("passed"))
            total = len(assertions)
            eval_record["configs"][config] = {
                "pass_rate": passes / total if total else 0.0,
                "passes": passes,
                "total": total,
                "tokens": timing.get("total_tokens"),
                "duration_ms": timing.get("duration_ms"),
            }
        bench["evals"].append(eval_record)

    # Aggregate
    by_config = {"with_skill": [], "without_skill": []}
    tokens_by_config = {"with_skill": [], "without_skill": []}
    durations_by_config = {"with_skill": [], "without_skill": []}
    for e in bench["evals"]:
        for cfg, stats in e["configs"].items():
            by_config[cfg].append(stats["pass_rate"])
            if stats["tokens"]:
                tokens_by_config[cfg].append(stats["tokens"])
            if stats["duration_ms"]:
                durations_by_config[cfg].append(stats["duration_ms"])

    bench["aggregate"] = {}
    for cfg in ("with_skill", "without_skill"):
        prs = by_config[cfg]
        toks = tokens_by_config[cfg]
        durs = durations_by_config[cfg]
        bench["aggregate"][cfg] = {
            "mean_pass_rate": statistics.mean(prs) if prs else 0,
            "stddev_pass_rate": statistics.stdev(prs) if len(prs) > 1 else 0,
            "mean_tokens": statistics.mean(toks) if toks else 0,
            "mean_duration_ms": statistics.mean(durs) if durs else 0,
            "n": len(prs),
        }
    bench["aggregate"]["delta_pass_rate"] = (
        bench["aggregate"]["with_skill"]["mean_pass_rate"]
        - bench["aggregate"]["without_skill"]["mean_pass_rate"]
    )

    (WS / "benchmark.json").write_text(json.dumps(bench, indent=2))

    # Markdown report
    md = ["# ACMI Skill Benchmark — Iteration 1", ""]
    md.append("## Aggregate")
    md.append("")
    md.append("| Config | Mean pass rate | Tokens (mean) | Duration (mean ms) | n |")
    md.append("|---|---|---|---|---|")
    for cfg in ("with_skill", "without_skill"):
        a = bench["aggregate"][cfg]
        md.append(f"| {cfg} | {a['mean_pass_rate']:.0%} | {a['mean_tokens']:.0f} | {a['mean_duration_ms']:.0f} | {a['n']} |")
    md.append(f"\n**Delta pass rate (with − without): {bench['aggregate']['delta_pass_rate']:+.0%}**\n")

    md.append("## Per-eval")
    md.append("")
    for e in bench["evals"]:
        md.append(f"### {e['eval_id']}")
        md.append("")
        md.append("| Config | Pass rate | Passes/Total | Tokens | Duration (ms) |")
        md.append("|---|---|---|---|---|")
        for cfg in ("with_skill", "without_skill"):
            s = e["configs"].get(cfg, {})
            md.append(f"| {cfg} | {s.get('pass_rate', 0):.0%} | {s.get('passes', 0)}/{s.get('total', 0)} | {s.get('tokens', '—')} | {s.get('duration_ms', '—')} |")
        md.append("")

    (WS / "benchmark.md").write_text("\n".join(md))
    print(json.dumps(bench["aggregate"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
