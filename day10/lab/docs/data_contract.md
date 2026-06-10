# Data Contract - Lab Day 10

Contract chi tiết nằm ở `contracts/data_contract.yaml`. File này ghi bản tóm tắt để đọc nhanh khi review artifact.

## 1. Nguồn Dữ Liệu

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|---|---|---|---|
| `policy_refund_v4` | CSV export từ policy/refund-v4 | stale refund window 14 ngày, duplicate chunk | `refund_no_stale_14d_window`, `hits_forbidden` |
| `sla_p1_2026` | CSV export từ support/sla-p1-2026 | duplicate chunk, missing effective date | top-1 doc match, ISO effective date |
| `it_helpdesk_faq` | CSV export từ support/helpdesk-faq | empty chunk, duplicate FAQ | chunk length, top-1 doc match |
| `hr_leave_policy` | CSV export từ hr/leave-policy-2026 | HR 2025 text nói 10 ngày phép năm | `stale_hr_policy_text`, `hr_leave_no_stale_10d_annual` |
| `access_control_sop` | CSV export từ it/access-control-sop | bị bỏ sót allowlist, duplicate Level 4 | `required_grading_doc_coverage`, top-1 doc match |

## 2. Schema Cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `chunk_id` | string | Có | ID ổn định sinh từ doc_id, nội dung, sequence |
| `doc_id` | string | Có | Một trong 5 canonical doc_ids |
| `chunk_text` | string | Có | Tối thiểu 8 ký tự, không mơ hồ |
| `effective_date` | date | Có | `YYYY-MM-DD`; hỗ trợ normalize `DD/MM/YYYY` |
| `exported_at` | datetime | Có | ISO datetime parseable |

## 3. Quarantine Vs Drop

Pipeline không drop im lặng. Mọi dòng bị loại được ghi vào `artifacts/quarantine/quarantine_<run_id>.csv` với `reason`: `unknown_doc_id`, `invalid_exported_at`, `missing_effective_date`, `stale_hr_policy_effective_date`, `stale_hr_policy_text`, `missing_chunk_text`, `ambiguous_chunk_text`, hoặc `duplicate_chunk_text`.

Run `final-pass` có `raw_records=247`, `cleaned_records=37`, `quarantine_records=210`.

## 4. Phiên Bản & Canonical

Refund canonical là `data/docs/policy_refund_v4.txt`, cửa sổ đúng là 7 ngày làm việc. HR canonical là `data/docs/hr_leave_policy.txt`, effective date tối thiểu `2026-01-01`, và câu hỏi dưới 3 năm kinh nghiệm phải trả về 12 ngày phép năm. Access-control canonical là `data/docs/access_control_sop.txt` và đã được thêm vào allowlist.
