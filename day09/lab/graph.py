"""
Day 09 supervisor-worker orchestrator.

Runs without LangGraph to keep the lab portable. The trace fields match the
required scoring format.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Optional, TypedDict

from workers.policy_tool import run as policy_tool_run
from workers.retrieval import run as retrieval_run
from workers.synthesis import run as synthesis_run


class AgentState(TypedDict, total=False):
    task: str
    route_reason: str
    risk_high: bool
    needs_tool: bool
    hitl_triggered: bool
    retrieved_chunks: list
    retrieved_sources: list
    policy_result: dict
    mcp_tools_used: list
    final_answer: str
    sources: list
    confidence: float
    history: list
    workers_called: list
    supervisor_route: str
    latency_ms: Optional[int]
    run_id: str
    worker_io_logs: list


def make_initial_state(task: str) -> AgentState:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return {
        "task": task,
        "route_reason": "",
        "risk_high": False,
        "needs_tool": False,
        "hitl_triggered": False,
        "retrieved_chunks": [],
        "retrieved_sources": [],
        "policy_result": {},
        "mcp_tools_used": [],
        "final_answer": "",
        "sources": [],
        "confidence": 0.0,
        "history": [],
        "workers_called": [],
        "supervisor_route": "",
        "latency_ms": None,
        "run_id": f"run_{stamp}",
        "worker_io_logs": [],
    }


def _contains(task: str, keywords: list[str]) -> bool:
    text = task.lower()
    return any(keyword in text for keyword in keywords)


def supervisor_node(state: AgentState) -> AgentState:
    task = state["task"]
    text = task.lower()
    state["history"].append(f"[supervisor] received task: {task[:100]}")

    policy_keywords = [
        "hoàn tiền", "hoan tien", "refund", "flash sale", "license",
        "subscription", "store credit", "cấp quyền", "cap quyen",
        "access", "level 2", "level 3", "admin access", "contractor",
    ]
    retrieval_keywords = ["p1", "sla", "ticket", "escalation", "remote", "mật khẩu", "mat khau"]
    risk_keywords = ["emergency", "khẩn cấp", "khan cap", "2am", "level 3", "err-"]

    route = "retrieval_worker"
    reason = "default retrieval route for factual KB lookup"
    needs_tool = False

    if _contains(text, policy_keywords):
        route = "policy_tool_worker"
        needs_tool = True
        reason = "task contains refund/access policy keyword; choose MCP-backed policy worker"
    elif _contains(text, retrieval_keywords):
        reason = "task contains SLA/FAQ/HR retrieval keyword; MCP not required"

    risk_high = _contains(text, risk_keywords)
    if risk_high:
        reason += " | risk_high flagged for trace visibility"

    if "err-" in text:
        route = "retrieval_worker"
        needs_tool = False
        reason = "unknown error code; retrieve first and abstain if no evidence"

    state["supervisor_route"] = route
    state["route_reason"] = reason
    state["needs_tool"] = needs_tool
    state["risk_high"] = risk_high
    state["history"].append(f"[supervisor] route={route} reason={reason}")
    return state


def human_review_node(state: AgentState) -> AgentState:
    state["hitl_triggered"] = True
    state["workers_called"].append("human_review")
    state["history"].append("[human_review] lab auto-approved")
    return state


def run_graph(task: str) -> AgentState:
    state = make_initial_state(task)
    start = time.time()

    state = supervisor_node(state)
    route = state["supervisor_route"]

    if route == "policy_tool_worker":
        state = retrieval_run(state)
        state = policy_tool_run(state)
    elif route == "human_review":
        state = human_review_node(state)
        state = retrieval_run(state)
    else:
        state = retrieval_run(state)

    state = synthesis_run(state)
    state["latency_ms"] = int((time.time() - start) * 1000)
    state["history"].append(f"[graph] completed in {state['latency_ms']}ms")
    return state


def save_trace(state: AgentState, output_dir: str = "./artifacts/traces") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{state['run_id']}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return filename


if __name__ == "__main__":
    tests = [
        "SLA xu ly ticket P1 la bao lau?",
        "Khach hang Flash Sale yeu cau hoan tien vi san pham loi - duoc khong?",
        "Contractor can Admin Access Level 3 de khac phuc P1 emergency. Quy trinh la gi?",
    ]
    for query in tests:
        result = run_graph(query)
        path = save_trace(result)
        print(f"\nQuery: {query}")
        print(f"Route: {result['supervisor_route']}")
        print(f"Reason: {result['route_reason']}")
        print(f"Workers: {result['workers_called']}")
        print(f"Answer: {result['final_answer']}")
        print(f"Trace: {path}")
