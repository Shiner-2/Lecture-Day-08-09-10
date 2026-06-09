# Single Agent vs Multi-Agent Comparison - Lab Day 09

**Nhom:** Day09 Lab  
**Ngay:** 2026-06-09

## 1. Metrics

Khong co artifact Day 08 baseline trong repo hien tai, nen bang duoi dung Day 09 trace thuc te va ghi `N/A` cho Day 08 thay vi tu bia so.

| Metric | Day 08 Single Agent | Day 09 Multi-Agent | Ghi chu |
|---|---:|---:|---|
| Total questions | N/A | 15 | `python eval_trace.py` |
| Success run rate | N/A | 15/15 | Khong crash |
| Avg confidence | N/A | 0.837 | Tu `artifacts/eval_report.json` |
| Avg latency | N/A | 114 ms | Local deterministic workers |
| MCP usage | N/A | 7/15 (46%) | Policy/access routes |
| HITL rate | N/A | 0/15 | HITL placeholder khong trigger |
| Routing visibility | Khong co route field | Co `route_reason` moi cau | De debug |
| Abstain case | N/A | q09 confidence 0.31 | ERR-403-AUTH khong co evidence |

## 2. Phan Tich Theo Loai Cau

Single-document questions nhu P1 SLA, password lock, remote policy di qua `retrieval_worker -> synthesis_worker`. Multi-agent khong tang do phuc tap cho nhom nay; trace ngan, latency thap, confidence thuong `0.88`.

Policy questions nhu Flash Sale, license key, store credit, Level 2/Level 3 access di qua `retrieval_worker -> policy_tool_worker -> synthesis_worker`. Loi duoc khoanh vung tot hon vi trace co `policy_result`, `exceptions_found`, va `mcp_tools_used`.

Multi-hop q15 dung ca SLA P1 va access SOP: trace goi `retrieval_worker`, `policy_tool_worker`, MCP `search_kb`, `check_access_permission`, `get_ticket_info`, sau do synthesis tra loi hai quy trinh song song.

## 3. Debuggability

Trong Day 09, khi answer sai co the doc ngay:

```text
supervisor_route -> route_reason -> workers_called -> worker_io_logs -> final_answer
```

Vi du q09 co route reason `unknown error code; retrieve first and abstain if no evidence`, confidence `0.31`, nen biet day la abstain co chu y, khong phai retrieval crash. Voi single-agent RAG, neu khong co trace tuong duong thi phai doc ca pipeline retrieve/generate de doan loi nam o dau.

## 4. Cost & Latency Trade-off

Ban lab hien tai khong goi LLM/API nen chi do duoc orchestration overhead local: average latency 114ms. Policy route cham hon retrieval route vi goi MCP mock va merge chunks, nhung doi lai co trace tool call. Simple query co 0 LLM call; complex query co 0 LLM call + 1-3 MCP calls.

## 5. Ket Luan

Multi-agent tot hon single-agent o kha nang debug va mo rong capability. Diem doi lai la can quan ly state/contract va routing rule. Voi cau hoi don gian chi can lookup mot tai lieu, single-agent hoac retrieval-only flow van du; multi-agent dang gia tri nhat khi cau hoi co exception, policy, access risk, hoac can external tool.
