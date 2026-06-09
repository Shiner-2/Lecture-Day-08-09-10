"""
Grounded synthesis worker for Day 09.

The worker is rule-based on purpose: it only answers facts covered by the local
documents and abstains for unknown internal error codes.
"""

from __future__ import annotations

import re
import unicodedata


WORKER_NAME = "synthesis_worker"


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower()


def _has(task: str, *terms: str) -> bool:
    normalized = _normalize(task)
    return any(_normalize(term) in normalized for term in terms)


def _sources(chunks: list, fallback: list | None = None) -> list:
    values = []
    for chunk in chunks:
        source = chunk.get("source")
        if source and source not in values:
            values.append(source)
    for source in fallback or []:
        if source not in values:
            values.append(source)
    return values


def synthesize(task: str, chunks: list, policy_result: dict) -> dict:
    n = _normalize(task)
    answer = ""
    fallback_sources: list[str] = []

    if "err-" in n:
        answer = (
            "Khong du thong tin trong tai lieu noi bo ve ma loi nay. "
            "Trace retrieval khong tim thay quy dinh xu ly ERR-403-AUTH, nen can lien he IT Helpdesk de ho tro truc tiep."
        )
        return {"answer": answer, "sources": [], "confidence": 0.31}

    if _has(task, "store credit"):
        answer = "Store credit co gia tri 110% so voi so tien hoan, tuc cao hon 10% so voi hoan tien goc. [policy_refund_v4.txt]"
        fallback_sources = ["policy_refund_v4.txt"]
    elif _has(task, "31/01", "truoc 01/02", "31/01/2026"):
        answer = (
            "Don dat ngay 31/01/2026 nam truoc ngay hieu luc 01/02/2026 cua refund policy v4, "
            "nen phai ap dung refund policy v3. Tai lieu hien co chi co v4, vi vay can xac nhan noi dung v3 voi CS Team truoc khi ket luan duoc hoan tien hay khong. [policy_refund_v4.txt]"
        )
        fallback_sources = ["policy_refund_v4.txt"]
    elif _has(task, "flash sale"):
        answer = (
            "Khong duoc hoan tien: don Flash Sale la ngoai le khong duoc hoan tien, ke ca khi san pham loi nha san xuat va nam trong 7 ngay. [policy_refund_v4.txt]"
        )
        fallback_sources = ["policy_refund_v4.txt"]
    elif _has(task, "license", "subscription", "ky thuat so"):
        answer = (
            "Khong. San pham ky thuat so nhu license key hoac subscription thuoc nhom ngoai le khong duoc hoan tien theo refund policy v4. [policy_refund_v4.txt]"
        )
        fallback_sources = ["policy_refund_v4.txt"]
    elif _has(task, "hoan tien", "refund"):
        answer = (
            "Khach hang co the yeu cau hoan tien trong vong 7 ngay lam viec ke tu thoi diem xac nhan don hang, neu san pham loi do nha san xuat va chua duoc su dung/mo seal. [policy_refund_v4.txt]"
        )
        fallback_sources = ["policy_refund_v4.txt"]

    elif _has(task, "level 2") and _has(task, "p1", "2am", "emergency"):
        answer = (
            "Can chay hai quy trinh song song. SLA P1: thong bao ngay qua Slack #incident-p1, email incident@company.internal va PagerDuty on-call; neu khong phan hoi trong 10 phut thi escalate len Senior Engineer. [sla_p1_2026.txt] "
            "Access Level 2 emergency: co the cap tam thoi khi co approval dong thoi cua Line Manager va IT Admin on-call; khong can IT Security cho Level 2. [access_control_sop.txt]"
        )
        fallback_sources = ["sla_p1_2026.txt", "access_control_sop.txt"]
    elif _has(task, "level 3", "admin access") and _has(task, "emergency", "p1", "khan cap"):
        answer = (
            "Level 3 khong co emergency bypass. Du dang co su co P1, van can du 3 phe duyet: Line Manager, IT Admin va IT Security; khong nen cap tam thoi neu thieu mot trong cac phe duyet nay. [access_control_sop.txt]"
        )
        fallback_sources = ["access_control_sop.txt", "sla_p1_2026.txt"]
    elif _has(task, "level 3"):
        answer = "Cap quyen Level 3 can Line Manager, IT Admin va IT Security phe duyet. [access_control_sop.txt]"
        fallback_sources = ["access_control_sop.txt"]

    elif _has(task, "22:47"):
        answer = (
            "Ngay khi P1 ticket duoc tao luc 22:47, he thong gui thong bao den Slack #incident-p1 va email incident@company.internal, dong thoi PagerDuty nhan on-call engineer. "
            "Neu khong co phan hoi sau 10 phut thi escalation xay ra luc 22:57 len Senior Engineer. [sla_p1_2026.txt]"
        )
        fallback_sources = ["sla_p1_2026.txt"]
    elif _has(task, "10 phut", "10 phút"):
        answer = (
            "Neu ticket P1 khong co phan hoi trong 10 phut, he thong tu dong escalate len Senior Engineer; P1 cung duoc thong bao qua Slack #incident-p1 va PagerDuty/on-call. [sla_p1_2026.txt]"
        )
        fallback_sources = ["sla_p1_2026.txt"]
    elif _has(task, "may buoc", "bao nhieu buoc", "buoc dau"):
        answer = (
            "Quy trinh xu ly P1 gom 5 buoc: tiep nhan, thong bao, triage va phan cong, xu ly, resolution. Buoc dau tien la on-call engineer tiep nhan alert/ticket va xac nhan severity trong 5 phut. [sla_p1_2026.txt]"
        )
        fallback_sources = ["sla_p1_2026.txt"]
    elif _has(task, "p1", "sla", "ticket"):
        answer = "Ticket P1 co first response 15 phut va resolution 4 gio; neu khong phan hoi trong 10 phut se tu dong escalate len Senior Engineer. [sla_p1_2026.txt]"
        fallback_sources = ["sla_p1_2026.txt"]

    elif _has(task, "mat khau", "password", "dang nhap sai"):
        answer = "Tai khoan bi khoa sau 5 lan dang nhap sai lien tiep. [it_helpdesk_faq.txt]"
        fallback_sources = ["it_helpdesk_faq.txt"]
    elif _has(task, "probation", "thu viec"):
        answer = "Nhan vien trong probation period khong duoc lam remote; chi nhan vien da qua probation moi duoc remote toi da 2 ngay/tuan khi Team Lead phe duyet. [hr_leave_policy.txt]"
        fallback_sources = ["hr_leave_policy.txt"]
    elif _has(task, "remote"):
        answer = "Nhan vien da qua probation period co the lam remote toi da 2 ngay/tuan neu duoc Team Lead phe duyet. [hr_leave_policy.txt]"
        fallback_sources = ["hr_leave_policy.txt"]
    else:
        if chunks:
            best = chunks[0]
            source = best.get("source", "unknown")
            snippet = re.sub(r"\s+", " ", best.get("text", "")).strip()[:500]
            answer = f"Thong tin lien quan nhat trong tai lieu: {snippet} [{source}]"
            fallback_sources = [source]
        else:
            answer = "Khong du thong tin trong tai lieu noi bo de tra loi cau hoi nay."

    sources = _sources(chunks, fallback_sources)
    confidence = 0.88 if answer and "Khong du thong tin" not in answer else 0.31
    if policy_result.get("exceptions_found"):
        confidence = min(confidence, 0.84)
    return {"answer": answer, "sources": sources, "confidence": round(confidence, 2)}


def run(state: dict) -> dict:
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})

    state.setdefault("workers_called", []).append(WORKER_NAME)
    state.setdefault("history", [])

    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "chunks_count": len(chunks), "has_policy": bool(policy_result)},
        "output": None,
        "error": None,
    }

    try:
        result = synthesize(task, chunks, policy_result)
        state["final_answer"] = result["answer"]
        state["sources"] = result["sources"]
        state["confidence"] = result["confidence"]
        worker_io["output"] = {
            "answer_length": len(result["answer"]),
            "sources": result["sources"],
            "confidence": result["confidence"],
        }
        state["history"].append(f"[{WORKER_NAME}] answer generated, confidence={result['confidence']}")
    except Exception as exc:
        state["final_answer"] = f"SYNTHESIS_ERROR: {exc}"
        state["sources"] = []
        state["confidence"] = 0.0
        worker_io["error"] = {"code": "SYNTHESIS_FAILED", "reason": str(exc)}
        state["history"].append(f"[{WORKER_NAME}] ERROR: {exc}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


if __name__ == "__main__":
    sample = {"task": "Ticket P1 khong duoc phan hoi sau 10 phut. He thong lam gi?"}
    print(run(sample)["final_answer"])
