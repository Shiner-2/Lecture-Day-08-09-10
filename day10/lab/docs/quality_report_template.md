# Quality Report - Lab Day 10

**run_id sạch:** `final-pass`  
**run_id inject:** `inject-bad`  
**Ngày:** 2026-06-10

## 1. Tóm Tắt Số Liệu

| Chỉ số | Inject bad | Sau fix | Ghi chú |
|---|---:|---:|---|
| raw_records | 247 | 247 | Cùng raw CSV |
| cleaned_records | 37 | 37 | Cùng số dòng, khác nội dung refund vì fix 14 -> 7 ngày |
| quarantine_records | 210 | 210 | Rule quarantine giống nhau |
| Expectation halt? | Có | Không | Inject fail `refund_no_stale_14d_window` với 2 violations |
| Grading pass | 9/10 sạch về forbidden | 10/10 | Inject có `gq_d10_01 hits_forbidden=true` |

## 2. Before / After Retrieval

Artifacts:

- Before/inject: `artifacts/eval/eval_after_inject_bad.csv`
- After/fix: `artifacts/eval/eval_after_fix.csv`
- Official grading: `artifacts/eval/grading_run.jsonl`

Kết quả then chốt:

| Câu hỏi | Inject bad | Sau fix |
|---|---|---|
| `q_refund_window` | `contains_expected=no`, `hits_forbidden=yes` | `contains_expected=yes`, `hits_forbidden=no` |
| `q_hr_annual_leave_under3` | `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes` | `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes` |
| `q_access_level4` | `contains_expected=yes`, `top1_doc_expected=yes` | `contains_expected=yes`, `top1_doc_expected=yes` |

Sau fix, 21/21 câu trong `eval_after_fix.csv` đều không có fail contains, không hit forbidden, và không fail top1.

## 3. Freshness & Monitor

Run `final-pass` ghi `latest_exported_at=2026-04-11T00:00:00`. Vì ngày chạy là 2026-06-10 và SLA là 24 giờ, freshness trả về `FAIL` với reason `freshness_sla_exceeded`. Đây là trạng thái hợp lý cho snapshot mẫu cũ; pipeline vẫn OK vì freshness được log để monitor, không dùng làm halt trong lab này.

## 4. Corruption Inject

Inject dùng lệnh:

```powershell
python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate
```

Flag `--no-refund-fix` cố ý giữ chunk refund stale 14 ngày. Expectation `refund_no_stale_14d_window` fail với 2 violations, nhưng `--skip-validate` cho phép publish index xấu để đo tác động. Eval sau đó chứng minh câu refund hit forbidden; chạy lại pipeline chuẩn loại lỗi này.

## 5. Hạn Chế & Việc Chưa Làm

- Chưa bật Chroma mặc định vì môi trường cục bộ thiếu dependency hoặc import chậm; backend local lexical được dùng để lab chạy ổn định.
- Chưa mở rộng allowlist cho `security_policy` và `data_privacy_guideline` vì không nằm trong bộ câu grading Day 10.
- Freshness hiện đo theo watermark trong manifest; bước tiếp theo nên thêm alert theo cả ingest time và publish time.
