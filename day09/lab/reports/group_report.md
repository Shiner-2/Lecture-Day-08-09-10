# Bao Cao Nhom - Lab Day 09: Multi-Agent Orchestration

**Ten nhom:** Day09 Lab
**Thanh vien:**

| Ten                 | Vai tro                                     | MSV         |
| ------------------- | ------------------------------------------- | ----------- |
| Pham Ngoc Hai Duong | Supervisor, Worker, MCP, Trace & Docs Owner | 2A202600629 |

**Ngay nop:** 2026-06-09
**Repo:** `Lecture-Day-08-09-10/day09/lab`

## 1. Kien Truc Da Xay Dung

Nhom xay dung he Supervisor-Worker gom mot supervisor trong `graph.py` va ba worker chinh: retrieval, policy/tool, synthesis. Supervisor doc cau hoi, gan `supervisor_route`, `route_reason`, `risk_high`, `needs_tool`, sau do dieu phoi. Cac cau SLA, FAQ, HR di qua `retrieval_worker`; cac cau refund/access/exception di qua `policy_tool_worker`; moi cau ket thuc o `synthesis_worker` de tao answer co citation va confidence.

Retrieval dung lexical search tren 5 tai lieu local trong `data/docs`, giup lab chay offline khong can API key hay Chroma. Policy worker xu ly Flash Sale, license/subscription, activated product, temporal scoping truoc 01/02/2026 va access Level 2/3. MCP server mock co `search_kb`, `get_ticket_info`, `check_access_permission`, `create_ticket`; trace q13/q15 co goi tool access permission.

## 2. Quyet Dinh Ky Thuat Quan Trong

Quyet dinh quan trong nhat la chon deterministic retrieval + rule-based synthesis thay vi goi LLM. Van de ban dau la skeleton phu thuoc embedding/Chroma/API key; neu thieu dependency thi retrieval co the rong hoac random, dan den trace kho cham. Phuong an LLM linh hoat hon nhung ton API key va kho on dinh trong lab. Phuong an lexical/rule-based kem tong quat hon, nhung chay duoc tren Windows local, khong hallucinate, va phu hop 15 cau test co domain ro.

Bang chung tu trace:

```text
total_traces: 15
routing_distribution: retrieval_worker 8/15, policy_tool_worker 7/15
avg_confidence: 0.837
avg_latency_ms: 114
mcp_usage_rate: 7/15
```

Vi du q13 route vao `policy_tool_worker` voi reason `task contains refund/access policy keyword; choose MCP-backed policy worker | risk_high flagged for trace visibility`, goi `search_kb`, `check_access_permission`, `get_ticket_info`, va tra loi Level 3 khong co emergency bypass.

## 3. Ket Qua Test Questions

Chay `python eval_trace.py` voi `data/test_questions.json`: 15/15 cau thanh cong, khong crash. Cau xu ly tot nhat la q15 vi can cross-doc: SLA P1 notification va Level 2 emergency access. Trace ghi du hai worker `retrieval_worker -> policy_tool_worker -> synthesis_worker` va MCP tools.

Cau abstain q09 duoc xu ly bang route retrieval va synthesis tra loi khong du thong tin ve `ERR-403-AUTH`, confidence 0.31. Cach nay tranh bia quy trinh khong co trong docs.

Chua chay `grading_questions.json` vi file khong co san trong repo tai thoi diem lam lab. Khi file public, co the dung `python eval_trace.py --grading` de tao `artifacts/grading_run.jsonl`.

## 4. So Sanh Day 08 vs Day 09

Repo hien tai khong co Day 08 eval artifact de lay baseline thuc te, nen nhom khong tu bia metric Day 08. Day 09 co cac metric that: average confidence 0.837, average latency 114ms, MCP usage 46%, HITL 0%. Thay doi ro nhat la debuggability: moi trace co `route_reason`, `workers_called`, `worker_io_logs`, `mcp_tools_used`.

Multi-agent khong can thiet cho cau hoi don gian nhu "SLA P1 la bao lau"; retrieval-only la du. Nhung voi policy/access, viec tach worker giup thay ro exception va tool output. Vi du q07 license key bi chan boi policy exception, q13 Level 3 emergency co `check_access_permission` lam bang chung.

## 5. Phan Cong Va Danh Gia

Do lam ca nhan trong workspace nay, Pham Ngoc Hai Duong phu trach tat ca cac module: supervisor, workers, MCP integration, eval trace va docs/report. Diem lam tot la uu tien he chay duoc end-to-end va trace doc duoc. Diem con han che la synthesis rule-based chua tong quat nhu LLM grounded generation; neu cau hoi an dung cach dien dat qua khac keyword thi can cai tien retrieval/rerank.

## 6. Neu Co Them 1 Ngay

Se them reranker nhe hoac BM25 chuan hon de tang precision source, va thay synthesis rule-based bang LLM grounded co guardrail "answer only from evidence". Ngoai ra se implement HITL checkpoint that cho cau `risk_high` co confidence thap.
