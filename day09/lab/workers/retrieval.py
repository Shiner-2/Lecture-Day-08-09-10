"""
Retrieval worker for Day 09.

This implementation uses deterministic lexical search over data/docs so the lab
can run without API keys, ChromaDB, or downloaded embedding models.
"""

from __future__ import annotations

import math
import re
import unicodedata
from pathlib import Path


WORKER_NAME = "retrieval_worker"
DEFAULT_TOP_K = 3
LAB_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = LAB_DIR / "data" / "docs"


ALIASES = {
    "p1": ["p1", "critical", "incident", "sla", "escalation", "pagerduty", "incident-p1"],
    "refund": ["refund", "hoan tien", "store credit", "flash sale", "license", "subscription"],
    "access": ["access", "quyen", "level", "admin", "contractor", "it admin", "security"],
    "remote": ["remote", "probation", "team lead", "leave", "hr"],
    "password": ["password", "mat khau", "dang nhap", "account", "khoa"],
}


DOC_HINTS = {
    "sla_p1_2026.txt": ["p1", "sla", "ticket", "incident", "escalation", "pagerduty", "22:47", "2am"],
    "policy_refund_v4.txt": ["refund", "hoan tien", "store credit", "flash sale", "license", "subscription"],
    "access_control_sop.txt": ["access", "quyen", "level", "admin", "contractor", "it admin", "security"],
    "it_helpdesk_faq.txt": ["password", "mat khau", "dang nhap", "account", "khoa", "err"],
    "hr_leave_policy.txt": ["remote", "probation", "leave", "nghi", "team lead"],
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower()


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9][a-z0-9\-]{1,}", _normalize(text)))


def _sections(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"\n(?====|[A-Z].{0,70}:|\d+\. )", text)
    sections = []
    for idx, part in enumerate(parts):
        clean = part.strip()
        if clean:
            sections.append({"text": clean, "source": path.name, "section": idx})
    return sections


def _expanded_query_tokens(query: str) -> set[str]:
    toks = _tokens(query)
    normalized = _normalize(query)
    for key, expansions in ALIASES.items():
        if key in toks or any(term in normalized for term in expansions):
            toks.update(_tokens(" ".join(expansions)))
    return toks


def retrieve_dense(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    query_tokens = _expanded_query_tokens(query)
    normalized_query = _normalize(query)
    if not query_tokens:
        return []

    candidates = []
    for path in sorted(DOCS_DIR.glob("*.txt")):
        doc_boost = 0
        for hint in DOC_HINTS.get(path.name, []):
            if hint in normalized_query:
                doc_boost += 2

        for section in _sections(path):
            section_tokens = _tokens(section["text"])
            overlap = query_tokens & section_tokens
            phrase_boost = sum(1 for tok in query_tokens if tok in _normalize(section["text"]))
            score = len(overlap) * 3 + phrase_boost + doc_boost
            if score <= 0:
                continue
            denom = math.sqrt(max(len(section_tokens), 1))
            candidates.append({
                "text": section["text"],
                "source": section["source"],
                "score": round(min(0.99, score / (denom + 8)), 4),
                "metadata": {"section": section["section"], "method": "lexical"},
            })

    candidates.sort(key=lambda item: (item["score"], item["source"]), reverse=True)

    selected = []
    seen_sources = set()
    for item in candidates:
        if item["source"] not in seen_sources:
            selected.append(item)
            seen_sources.add(item["source"])
        if len(selected) >= top_k:
            break

    for item in candidates:
        if len(selected) >= top_k:
            break
        if item not in selected:
            selected.append(item)

    return selected[:top_k]


def run(state: dict) -> dict:
    task = state.get("task", "")
    top_k = int(state.get("retrieval_top_k", DEFAULT_TOP_K))

    state.setdefault("workers_called", []).append(WORKER_NAME)
    state.setdefault("history", [])

    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "top_k": top_k},
        "output": None,
        "error": None,
    }

    try:
        chunks = retrieve_dense(task, top_k)
        sources = []
        for chunk in chunks:
            if chunk["source"] not in sources:
                sources.append(chunk["source"])

        state["retrieved_chunks"] = chunks
        state["retrieved_sources"] = sources
        worker_io["output"] = {"chunks_count": len(chunks), "sources": sources}
        state["history"].append(f"[{WORKER_NAME}] retrieved {len(chunks)} chunks from {sources}")
    except Exception as exc:
        state["retrieved_chunks"] = []
        state["retrieved_sources"] = []
        worker_io["error"] = {"code": "RETRIEVAL_FAILED", "reason": str(exc)}
        state["history"].append(f"[{WORKER_NAME}] ERROR: {exc}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


if __name__ == "__main__":
    for query in [
        "SLA ticket P1 la bao lau?",
        "Store credit khi hoan tien la bao nhieu?",
        "Ai phe duyet cap quyen Level 3?",
    ]:
        result = run({"task": query})
        print(query)
        for chunk in result["retrieved_chunks"]:
            preview = chunk["text"][:90].encode("ascii", "ignore").decode("ascii")
            print(f"  {chunk['score']:.2f} {chunk['source']}: {preview}")
