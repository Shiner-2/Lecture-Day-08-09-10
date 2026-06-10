# Báo Cáo Cá Nhân - Lab Day 10

**Họ và tên:** Phạm Ngọc Hải Dương  
**Vai trò:** Cleaning / Quality / Embed / Monitoring  
**Ngày nộp:** 2026-06-10  
**Run chính:** `final-pass`

## 1. Tôi phụ trách phần nào?

Tôi phụ trách hoàn thiện pipeline dữ liệu trong `day10/lab`, tập trung vào các file `transform/cleaning_rules.py`, `quality/expectations.py`, `etl_pipeline.py`, `eval_retrieval.py`, `grading_run.py`, và tài liệu trong `docs/`. Phần việc chính là biến raw CSV 247 dòng thành một snapshot sạch có thể dùng cho retrieval: 37 dòng cleaned, 210 dòng quarantine, có manifest và log đầy đủ. Tôi cũng thêm fallback local index trong `retrieval_backend.py` để lab chạy được trên máy hiện tại khi `chromadb` hoặc model embedding chưa sẵn sàng.

## 2. Một quyết định kỹ thuật

Quyết định quan trọng nhất là giữ các lỗi version policy ở mức `halt`, còn freshness chỉ ghi monitor. Ví dụ `refund_no_stale_14d_window`, `hr_leave_no_stale_10d_annual`, `required_grading_doc_coverage`, và `exported_at_iso_datetime` đều là halt vì nếu fail thì index sẽ trả lời sai trực tiếp. Ngược lại, run `final-pass` có freshness `FAIL` do `latest_exported_at=2026-04-11T00:00:00` đã quá SLA 24 giờ khi chạy ngày 2026-06-10. Đây là cảnh báo vận hành của snapshot mẫu, không phải lỗi clean làm sai câu trả lời, nên pipeline vẫn ghi `PIPELINE_OK`.

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly rõ nhất là baseline bỏ sót `access_control_sop` trong allowlist và còn lọt HR 2025 text. Baseline có `cleaned_records=40`, `quarantine_records=207`, nhưng expectation HR fail với 2 violations. Tôi thêm `access_control_sop` vào `ALLOWED_DOC_IDS`, thêm rule `stale_hr_policy_text` để loại các dòng “10 ngày phép năm (bản HR 2025)” kể cả khi effective date là 2026, và thêm rule `invalid_exported_at` để không publish timestamp export sai format. Sau fix, `run_final-pass.log` ghi `required_grading_doc_coverage OK`, `hr_leave_no_stale_10d_annual OK`, `exported_at_iso_datetime OK`.

## 4. Bằng chứng trước / sau

Trước fix có inject run:

```text
run_id=inject-bad
expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=2
```

`artifacts/eval/eval_after_inject_bad.csv` cho thấy `q_refund_window contains_expected=no` và `hits_forbidden=yes`. Sau khi chạy `final-pass`, `artifacts/eval/eval_after_fix.csv` đạt 21/21 không forbidden, còn `artifacts/eval/grading_run.jsonl` đạt đủ 10 câu. Quick check cuối báo mọi `GRADE_CHECK[gq_d10_01]` đến `GRADE_CHECK[gq_d10_10]` đều OK.

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ thêm kiểm thử tự động cho từng cleaning reason và chạy dual backend: local lexical để smoke test nhanh, Chroma để so sánh ranking embedding thật. Tôi cũng sẽ thêm freshness ở hai boundary ingest và publish để phân biệt source cũ với pipeline chậm.
