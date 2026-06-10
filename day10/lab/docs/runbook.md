# Runbook - Lab Day 10

## Symptom

Agent hoặc retrieval trả lời sai version, ví dụ refund là 14 ngày thay vì 7 ngày, HR dưới 3 năm là 10 ngày phép năm thay vì 12 ngày, hoặc câu Level 4 Admin Access không tìm thấy IT Manager/CISO.

## Detection

Chạy:

```powershell
python etl_pipeline.py run --run-id final-pass
python eval_retrieval.py --out artifacts/eval/eval_after_fix.csv
python grading_run.py --out artifacts/eval/grading_run.jsonl
python instructor_quick_check.py --grading artifacts/eval/grading_run.jsonl --manifest artifacts/manifests/manifest_final-pass.json
```

Các tín hiệu chính: expectation `FAIL (halt)`, `hits_forbidden=yes`, `contains_expected=no`, hoặc `top1_doc_matches=false`.

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|---|---|---|
| 1 | Kiểm tra `artifacts/logs/run_<run_id>.log` | Có `raw_records`, `cleaned_records`, `quarantine_records`, expectation status |
| 2 | Mở `artifacts/quarantine/quarantine_<run_id>.csv` | Thấy reason cụ thể cho dòng bị loại |
| 3 | Mở manifest | Xác nhận cleaned CSV, run_id, latest_exported_at |
| 4 | Chạy eval/grading | Xác định câu nào còn fail hoặc hit forbidden |
| 5 | So sánh inject vs clean | `eval_after_inject_bad.csv` phải xấu hơn `eval_after_fix.csv` |

## Mitigation

Nếu expectation halt, không publish index trừ khi đang demo Sprint 3 với `--skip-validate`. Sửa rule ở `transform/cleaning_rules.py`, chạy lại pipeline bằng run_id mới, sau đó rerun eval/grading. Nếu index bị publish từ inject bad, chạy lại `python etl_pipeline.py run --run-id final-pass` để restore snapshot sạch.

## Prevention

- Giữ `required_grading_doc_coverage` để phát hiện thiếu nguồn như `access_control_sop`.
- Giữ `refund_no_stale_14d_window` và `hr_leave_no_stale_10d_annual` ở severity `halt`.
- Kiểm tra `exported_at_iso_datetime` trước freshness để không có watermark sai format.
- Lưu evidence before/after sau mỗi thay đổi rule lớn.
- Nếu chuyển sang Chroma, đặt `DAY10_EMBED_BACKEND=chroma` và kiểm tra prune id cũ sau publish.
