"""Policy/tool worker with in-process mock MCP calls."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


WORKER_NAME = "policy_tool_worker"
LAB_DIR = Path(__file__).resolve().parents[1]
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _call_mcp_tool(tool_name: str, tool_input: dict) -> dict:
    try:
        from mcp_server import dispatch_tool

        output = dispatch_tool(tool_name, tool_input)
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": output,
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as exc:
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": None,
            "error": {"code": "MCP_CALL_FAILED", "reason": str(exc)},
            "timestamp": datetime.now().isoformat(),
        }


def analyze_policy(task: str, chunks: list) -> dict:
    task_lower = task.lower()
    exceptions = []
    policy_name = "general_kb"
    policy_applies = True
    version_note = ""

    if any(kw in task_lower for kw in ["hoàn tiền", "hoan tien", "refund", "flash sale", "license", "store credit"]):
        policy_name = "refund_policy_v4"

    if "flash sale" in task_lower:
        exceptions.append({
            "type": "flash_sale_exception",
            "rule": "Flash Sale is a refund exclusion in refund policy v4.",
            "source": "policy_refund_v4.txt",
        })
    if any(kw in task_lower for kw in ["license", "subscription", "kỹ thuật số", "ky thuat so"]):
        exceptions.append({
            "type": "digital_product_exception",
            "rule": "Digital products such as license keys/subscriptions are refund exclusions.",
            "source": "policy_refund_v4.txt",
        })
    if any(kw in task_lower for kw in ["đã kích hoạt", "da kich hoat", "đã sử dụng", "da su dung"]):
        exceptions.append({
            "type": "activated_product_exception",
            "rule": "Activated or used products are refund exclusions.",
            "source": "policy_refund_v4.txt",
        })
    if any(kw in task_lower for kw in ["31/01", "30/01", "trước 01/02", "truoc 01/02"]):
        version_note = "Order date is before 2026-02-01, so refund policy v3 applies; current docs only include v4."

    if any(kw in task_lower for kw in ["level 2", "level 3", "admin access", "access", "cấp quyền", "cap quyen"]):
        policy_name = "access_control_sop"

    if exceptions:
        policy_applies = False

    sources = []
    for chunk in chunks:
        source = chunk.get("source")
        if source and source not in sources:
            sources.append(source)

    return {
        "policy_applies": policy_applies,
        "policy_name": policy_name,
        "exceptions_found": exceptions,
        "source": sources,
        "policy_version_note": version_note,
        "explanation": "Analyzed via deterministic rule-based policy check.",
    }


def run(state: dict) -> dict:
    task = state.get("task", "")
    task_lower = task.lower()
    chunks = state.get("retrieved_chunks", [])
    needs_tool = state.get("needs_tool", False)

    state.setdefault("workers_called", []).append(WORKER_NAME)
    state.setdefault("history", [])
    state.setdefault("mcp_tools_used", [])

    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "chunks_count": len(chunks), "needs_tool": needs_tool},
        "output": None,
        "error": None,
    }

    try:
        if needs_tool:
            search_result = _call_mcp_tool("search_kb", {"query": task, "top_k": 3})
            state["mcp_tools_used"].append(search_result)
            state["history"].append(f"[{WORKER_NAME}] called MCP search_kb")
            search_output = search_result.get("output") or {}
            if search_output.get("chunks"):
                merged = {(c.get("source"), c.get("text", "")[:80]): c for c in chunks}
                for chunk in search_output["chunks"]:
                    merged[(chunk.get("source"), chunk.get("text", "")[:80])] = chunk
                chunks = list(merged.values())
                state["retrieved_chunks"] = chunks
                state["retrieved_sources"] = list({c.get("source", "unknown") for c in chunks})

        policy_result = analyze_policy(task, chunks)

        if needs_tool and any(kw in task_lower for kw in ["level 2", "level 3", "admin access", "access", "cấp quyền", "cap quyen"]):
            access_level = 3 if ("level 3" in task_lower or "admin access" in task_lower) else 2
            access_result = _call_mcp_tool(
                "check_access_permission",
                {
                    "access_level": access_level,
                    "requester_role": "contractor" if "contractor" in task_lower else "employee",
                    "is_emergency": any(kw in task_lower for kw in ["p1", "emergency", "khẩn cấp", "khan cap", "2am"]),
                },
            )
            state["mcp_tools_used"].append(access_result)
            policy_result["access_check"] = access_result.get("output")
            state["history"].append(f"[{WORKER_NAME}] called MCP check_access_permission")

        if needs_tool and any(kw in task_lower for kw in ["ticket", "p1", "jira"]):
            ticket_result = _call_mcp_tool("get_ticket_info", {"ticket_id": "P1-LATEST"})
            state["mcp_tools_used"].append(ticket_result)
            policy_result["ticket_info"] = ticket_result.get("output")
            state["history"].append(f"[{WORKER_NAME}] called MCP get_ticket_info")

        state["policy_result"] = policy_result
        worker_io["output"] = {
            "policy_name": policy_result["policy_name"],
            "policy_applies": policy_result["policy_applies"],
            "exceptions_count": len(policy_result["exceptions_found"]),
            "mcp_calls": len(state["mcp_tools_used"]),
        }
        state["history"].append(
            f"[{WORKER_NAME}] policy={policy_result['policy_name']} exceptions={len(policy_result['exceptions_found'])}"
        )
    except Exception as exc:
        state["policy_result"] = {"error": str(exc)}
        worker_io["error"] = {"code": "POLICY_CHECK_FAILED", "reason": str(exc)}
        state["history"].append(f"[{WORKER_NAME}] ERROR: {exc}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


if __name__ == "__main__":
    result = run({"task": "Level 3 access emergency cho contractor", "needs_tool": True})
    print(result["policy_result"])
    print(result.get("mcp_tools_used", []))
