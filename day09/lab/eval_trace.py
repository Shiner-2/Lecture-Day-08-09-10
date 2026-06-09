"""Trace runner/evaluator for Day 09 lab."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LAB_DIR = Path(__file__).resolve().parent
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))

from graph import run_graph, save_trace


def _load_json(path: str | Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_test_questions(questions_file: str = "data/test_questions.json") -> list:
    questions = _load_json(questions_file)
    print(f"\nRunning {len(questions)} test questions from {questions_file}")
    print("=" * 60)

    results = []
    for idx, q in enumerate(questions, 1):
        qid = q.get("id", f"q{idx:02d}")
        question = q["question"]
        print(f"[{idx:02d}/{len(questions)}] {qid}: {question[:65]}...")
        try:
            result = run_graph(question)
            result["question_id"] = qid
            save_trace(result, "artifacts/traces")
            print(f"  OK route={result.get('supervisor_route')} conf={result.get('confidence'):.2f} {result.get('latency_ms')}ms")
            results.append({"id": qid, "question": question, "result": result})
        except Exception as exc:
            print(f"  ERROR: {exc}")
            results.append({"id": qid, "question": question, "error": str(exc), "result": None})

    succeeded = sum(1 for item in results if item.get("result"))
    print(f"\nDone. {succeeded}/{len(results)} succeeded.")
    return results


def run_grading_questions(questions_file: str = "data/grading_questions.json") -> str:
    if not os.path.exists(questions_file):
        print(f"{questions_file} is not available yet.")
        return ""

    questions = _load_json(questions_file)
    os.makedirs("artifacts", exist_ok=True)
    output_file = "artifacts/grading_run.jsonl"

    with open(output_file, "w", encoding="utf-8") as out:
        for idx, q in enumerate(questions, 1):
            qid = q.get("id", f"gq{idx:02d}")
            question = q["question"]
            try:
                result = run_graph(question)
                record = {
                    "id": qid,
                    "question": question,
                    "answer": result.get("final_answer", "PIPELINE_ERROR: no answer"),
                    "sources": result.get("retrieved_sources", []),
                    "supervisor_route": result.get("supervisor_route", ""),
                    "route_reason": result.get("route_reason", ""),
                    "workers_called": result.get("workers_called", []),
                    "mcp_tools_used": [tool.get("tool") for tool in result.get("mcp_tools_used", [])],
                    "confidence": result.get("confidence", 0.0),
                    "hitl_triggered": result.get("hitl_triggered", False),
                    "latency_ms": result.get("latency_ms"),
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as exc:
                record = {
                    "id": qid,
                    "question": question,
                    "answer": f"PIPELINE_ERROR: {exc}",
                    "sources": [],
                    "supervisor_route": "error",
                    "route_reason": str(exc),
                    "workers_called": [],
                    "mcp_tools_used": [],
                    "confidence": 0.0,
                    "hitl_triggered": False,
                    "latency_ms": None,
                    "timestamp": datetime.now().isoformat(),
                }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"wrote {qid}")

    return output_file


def analyze_traces(traces_dir: str = "artifacts/traces") -> dict:
    traces_path = Path(traces_dir)
    if not traces_path.exists():
        return {}

    traces = [_load_json(path) for path in sorted(traces_path.glob("*.json"))]
    if not traces:
        return {}

    routing_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    confidences = []
    latencies = []
    mcp_count = 0
    hitl_count = 0

    for trace in traces:
        route = trace.get("supervisor_route", "unknown")
        routing_counts[route] = routing_counts.get(route, 0) + 1
        if trace.get("confidence") is not None:
            confidences.append(float(trace.get("confidence", 0)))
        if trace.get("latency_ms") is not None:
            latencies.append(int(trace["latency_ms"]))
        if trace.get("mcp_tools_used"):
            mcp_count += 1
        if trace.get("hitl_triggered"):
            hitl_count += 1
        for source in trace.get("retrieved_sources", []):
            source_counts[source] = source_counts.get(source, 0) + 1

    total = len(traces)
    return {
        "total_traces": total,
        "routing_distribution": {k: f"{v}/{total} ({100*v//total}%)" for k, v in routing_counts.items()},
        "avg_confidence": round(sum(confidences) / len(confidences), 3) if confidences else 0,
        "avg_latency_ms": round(sum(latencies) / len(latencies)) if latencies else 0,
        "mcp_usage_rate": f"{mcp_count}/{total} ({100*mcp_count//total}%)",
        "hitl_rate": f"{hitl_count}/{total} ({100*hitl_count//total}%)",
        "top_sources": sorted(source_counts.items(), key=lambda item: -item[1])[:5],
    }


def compare_single_vs_multi(multi_traces_dir: str = "artifacts/traces", day08_results_file: str | None = None) -> dict:
    day08_baseline = {
        "total_questions": "N/A",
        "avg_confidence": "N/A",
        "avg_latency_ms": "N/A",
        "abstain_rate": "N/A",
        "multi_hop_accuracy": "N/A",
    }
    if day08_results_file and os.path.exists(day08_results_file):
        day08_baseline = _load_json(day08_results_file)

    return {
        "generated_at": datetime.now().isoformat(),
        "day08_single_agent": day08_baseline,
        "day09_multi_agent": analyze_traces(multi_traces_dir),
        "analysis": {
            "routing_visibility": "Day 09 has route_reason for every trace, so failures are easier to debug.",
            "latency_delta": "N/A because no Day 08 baseline artifact is present in this repo.",
            "accuracy_delta": "N/A until grading_questions.json and Day 08 baseline are both available.",
            "debuggability": "Workers can be tested independently through worker_io_logs and workers_called.",
            "mcp_benefit": "Policy/access capabilities are added through MCP tools without changing the supervisor core.",
        },
    }


def save_eval_report(comparison: dict) -> str:
    os.makedirs("artifacts", exist_ok=True)
    output_file = "artifacts/eval_report.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    return output_file


def print_metrics(metrics: dict) -> None:
    print("\nTrace Analysis:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 09 trace evaluation")
    parser.add_argument("--grading", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--test-file", default="data/test_questions.json")
    args = parser.parse_args()

    if args.grading:
        path = run_grading_questions()
        if path:
            print(f"Grading log saved: {path}")
    elif args.analyze:
        print_metrics(analyze_traces())
    elif args.compare:
        report = save_eval_report(compare_single_vs_multi())
        print(f"Comparison report saved: {report}")
    else:
        run_test_questions(args.test_file)
        metrics = analyze_traces()
        print_metrics(metrics)
        report = save_eval_report(compare_single_vs_multi())
        print(f"\nEval report: {report}")
