# System Architecture - Lab Day 09

**Nhom:** Day09 Lab  
**Ngay:** 2026-06-09  
**Version:** 1.0

## 1. Tong Quan

He thong dung pattern **Supervisor-Worker**. `graph.py` nhan cau hoi, gan `supervisor_route`, `route_reason`, `risk_high`, `needs_tool`, sau do goi worker phu hop. Cac cau tra cuu SLA/FAQ/HR di qua `retrieval_worker`; cac cau refund/access/exception di qua `policy_tool_worker` co MCP; tat ca deu ket thuc bang `synthesis_worker`.

Ly do chon pattern nay thay vi single agent: trace tach ro loi routing, retrieval, policy va synthesis; moi worker co contract rieng; them tool ngoai qua MCP khong can sua toan bo pipeline.

## 2. So Do Pipeline

```text
User question
  -> Supervisor (route_reason, risk_high, needs_tool)
      -> retrieval_worker
          -> synthesis_worker
      -> retrieval_worker -> policy_tool_worker -> MCP tools
          -> synthesis_worker
      -> human_review (reserved) -> retrieval_worker -> synthesis_worker
  -> final_answer + sources + confidence + JSON trace
```

## 3. Vai Tro Thanh Phan

| Thanh phan | Nhiem vu | Input | Output |
|---|---|---|---|
| `graph.py` | Dieu phoi supervisor-worker bang rule routing | `task` | `supervisor_route`, `route_reason`, trace state |
| `workers/retrieval.py` | Search lexical deterministic tren `data/docs/*.txt` | `task`, `top_k` | `retrieved_chunks`, `retrieved_sources` |
| `workers/policy_tool.py` | Phan tich refund/access policy, exception va goi MCP | `task`, chunks, `needs_tool` | `policy_result`, `mcp_tools_used` |
| `workers/synthesis.py` | Tong hop answer grounded co citation, abstain khi thieu evidence | chunks, policy_result | `final_answer`, `sources`, `confidence` |
| `mcp_server.py` | Mock MCP server | tool name + JSON input | JSON tool output |

MCP tools da implement: `search_kb`, `get_ticket_info`, `check_access_permission`, `create_ticket`.

## 4. Shared State Schema

| Field | Type | Doc/Ghi |
|---|---|---|
| `task` | str | Cau hoi dau vao |
| `supervisor_route` | str | Supervisor ghi worker duoc chon |
| `route_reason` | str | Supervisor ghi ly do route |
| `risk_high` | bool | Supervisor gan khi co P1/emergency/Level 3/ERR |
| `needs_tool` | bool | Supervisor gan cho cau policy/access |
| `retrieved_chunks` | list | Retrieval/MCP ghi, synthesis doc |
| `retrieved_sources` | list | Retrieval/MCP ghi |
| `policy_result` | dict | Policy worker ghi |
| `mcp_tools_used` | list | Policy worker ghi tool calls |
| `workers_called` | list | Moi worker append |
| `final_answer` | str | Synthesis ghi |
| `confidence` | float | Synthesis ghi |
| `worker_io_logs` | list | Moi worker ghi input/output/error |

## 5. Ket Qua Kien Truc

Lan chay `python eval_trace.py` sinh 15 trace thanh cong: 8/15 route `retrieval_worker`, 7/15 route `policy_tool_worker`, MCP duoc dung 7/15 cau, average confidence 0.837, average latency 114ms, HITL 0/15.

## 6. Gioi Han

1. Retrieval lexical on dinh va offline nhung kem semantic embedding khi cau hoi viet qua khac keyword.
2. Synthesis rule-based phu hop lab public questions, nhung chua linh hoat nhu LLM grounded generation.
3. `human_review` moi la placeholder; neu production can checkpoint/approval that.
