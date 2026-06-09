# Routing Decisions Log - Lab Day 09

**Nhom:** Day09 Lab  
**Ngay:** 2026-06-09

Nguon: trace sinh tu `python eval_trace.py` trong `artifacts/traces/`.

## Routing Decision #1

**Task dau vao:** "SLA xử lý ticket P1 là bao lâu?"

**Worker duoc chon:** `retrieval_worker`  
**Route reason:** `task contains SLA/FAQ/HR retrieval keyword; MCP not required`  
**MCP tools:** none  
**Workers called:** `retrieval_worker -> synthesis_worker`

**Ket qua:** Tra loi P1 first response 15 phut, resolution 4 gio, escalation 10 phut. Confidence `0.88`. Routing dung vi day la cau factual retrieval tu `sla_p1_2026.txt`.

## Routing Decision #2

**Task dau vao:** "Sản phẩm kỹ thuật số (license key) có được hoàn tiền không?"

**Worker duoc chon:** `policy_tool_worker`  
**Route reason:** `task contains refund/access policy keyword; choose MCP-backed policy worker`  
**MCP tools:** `search_kb`  
**Workers called:** `retrieval_worker -> policy_tool_worker -> synthesis_worker`

**Ket qua:** Tra loi khong duoc hoan tien vi license/subscription la exception cua refund policy v4. Confidence `0.84`. Routing dung vi can policy exception detection, khong chi retrieve.

## Routing Decision #3

**Task dau vao:** "Contractor cần Admin Access (Level 3) để khắc phục sự cố P1 đang active..."

**Worker duoc chon:** `policy_tool_worker`  
**Route reason:** `task contains refund/access policy keyword; choose MCP-backed policy worker | risk_high flagged for trace visibility`  
**MCP tools:** `search_kb`, `check_access_permission`, `get_ticket_info`  
**Workers called:** `retrieval_worker -> policy_tool_worker -> synthesis_worker`

**Ket qua:** Tra loi Level 3 khong co emergency bypass, van can Line Manager, IT Admin va IT Security. Confidence `0.88`. Routing dung vi cau nay vua co access policy vua co risk P1.

## Routing Decision #4

**Task dau vao:** "ERR-403-AUTH là lỗi gì và cách xử lý?"

**Worker duoc chon:** `retrieval_worker`  
**Route reason:** `unknown error code; retrieve first and abstain if no evidence`  
**MCP tools:** none  
**Workers called:** `retrieval_worker -> synthesis_worker`

**Ket qua:** He thong abstain: khong du thong tin trong tai lieu noi bo ve ma loi nay. Confidence `0.31`. Day la routing kho vi co risk keyword `ERR-`, nhung chon retrieval truoc de tranh hallucination.

## Tong Ket

| Worker | So cau | Ty le |
|---|---:|---:|
| `retrieval_worker` | 8/15 | 53% |
| `policy_tool_worker` | 7/15 | 46% |
| `human_review` | 0/15 | 0% |

Routing accuracy tren `test_questions.json`: 15/15 cau chay thanh cong; cac route quan trong khop expected intent. Route reason du de debug vi ghi ca signal chon worker va risk flag.
