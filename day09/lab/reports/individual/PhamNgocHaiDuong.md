# Bao Cao Ca Nhan - Pham Ngoc Hai Duong

## Phan toi phu trach

Trong lab Day 09, toi phu trach toan bo phan supervisor-worker pipeline trong workspace: `graph.py`, ba worker trong `workers/`, MCP mock server integration, `eval_trace.py` va cac tai lieu tong ket. Phan code quan trong nhat la bien skeleton placeholder thanh he chay duoc end-to-end voi 15 cau test. `graph.py` nhan cau hoi, gan `supervisor_route`, `route_reason`, `risk_high`, `needs_tool`, sau do goi `retrieval_worker`, `policy_tool_worker` va `synthesis_worker` theo dung thu tu. `retrieval_worker` search tren 5 tai lieu local trong `data/docs`; `policy_tool_worker` phan tich refund/access exception va goi MCP; `synthesis_worker` tao cau tra loi grounded co citation va confidence.

## Mot quyet dinh ky thuat

Quyet dinh toi chon la dung deterministic lexical retrieval va rule-based synthesis thay vi phu thuoc LLM/API key. Ly do la skeleton ban dau co nguy co fail neu thieu ChromaDB, embedding model, OpenAI key hoac Google key. Voi lab can nop trace va chay grading nhanh, he on dinh quan trong hon cau tra loi hoa my. Trade-off la he kem tong quat neu cau hoi viet qua khac keyword, nhung doi lai `python eval_trace.py` chay offline, nhanh, trace ro va tranh hallucination. Ket qua thuc te: 15/15 test questions succeeded, avg confidence 0.837, avg latency 114ms, MCP usage 7/15.

## Mot loi da sua

Loi lon nhat trong qua trinh lam la Windows PowerShell dung cp1252 nen crash khi in emoji hoac tieng Viet tu trace/doc. Ban dau `eval_trace.py` da chay qua cac cau hoi, nhung crash khi doc lai JSON trace bang encoding mac dinh. Toi sua bang cach reconfigure stdout sang UTF-8 va mo file trace voi `encoding="utf-8"`. Mot loi khac la `policy_tool.py` khi chay standalone khong import duoc `mcp_server` vi `sys.path` dang tro vao folder `workers`; toi them duong dan lab vao `sys.path`. Sau khi sua, `python eval_trace.py`, `python workers/policy_tool.py` va `python mcp_server.py` deu chay duoc.

## Tu danh gia

Toi lam tot o viec dua he ve trang thai co the cham duoc: route co reason, worker co IO log, MCP calls co input/output, docs dung so lieu trace that. Diem yeu la retrieval lexical source precision chua hoan hao: doi khi chunk phu tu FAQ/HR xuat hien trong top sources do keyword chung. Tuy nhien synthesis van uu tien rule dung theo task nen answer cua 15 cau public van dung muc tieu. Nhom phu thuoc vao toi o phan ket noi end-to-end va debugging Windows/path/encoding.

## Neu co them 2 gio

Toi se cai tien retrieval bang BM25 hoac scoring theo document intent manh hon de top sources gon hon, dac biet cho access questions. Toi cung se them mot evaluator nho so sanh `expected_sources` va `expected_route` trong `test_questions.json` de in routing accuracy/source hit rate thay vi chi in latency/confidence.
