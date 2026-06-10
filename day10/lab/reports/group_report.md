# Báo Cáo Nhóm - Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Day10 data pipeline group  
**Ngày nộp:** 2026-06-10  
**Repo:** `day10/lab`  
**Run cuối:** `final-pass`

| Tên | Vai trò (Day 10) | Email |
|---|---|---|
| Phạm Ngọc Hải Dương | Cleaning, Quality, Embed, Monitoring | _ |

## 1. Pipeline Tổng Quan

Pipeline đọc `data/raw/policy_export_dirty.csv` gồm 247 raw records, clean dữ liệu theo allowlist/canonical version, ghi quarantine, chạy expectation suite, rồi publish index phục vụ retrieval. Luồng chạy một dòng:

```powershell
python etl_pipeline.py run --run-id final-pass; python eval_retrieval.py --out artifacts/eval/eval_after_fix.csv; python grading_run.py --out artifacts/eval/grading_run.jsonl
```

Run `final-pass` tạo `artifacts/cleaned/cleaned_final-pass.csv`, `artifacts/quarantine/quarantine_final-pass.csv`, `artifacts/manifests/manifest_final-pass.json`, và `artifacts/local_index/day10_kb.json`. Kết quả cuối: `raw_records=247`, `cleaned_records=37`, `quarantine_records=210`, `PIPELINE_OK`. Backend publish mặc định là local lexical index để không phụ thuộc Chroma trong máy lab; nếu muốn dùng Chroma có thể đặt `DAY10_EMBED_BACKEND=chroma`.

## 2. Cleaning & Expectation

Nhóm sửa pipeline để nhận đủ 5 nguồn grading, đặc biệt thêm `access_control_sop` vào allowlist. Các rule quan trọng gồm: normalize `effective_date`, quarantine unknown doc_id, quarantine timestamp export sai ISO, quarantine HR 2025 theo nội dung “10 ngày phép năm”, quarantine chunk mơ hồ, dedupe normalized chunk text, và fix refund stale 14 ngày thành 7 ngày.

### 2a. Bảng metric_impact

| Rule / Expectation mới | Trước | Sau / khi inject | Chứng cứ |
|---|---|---|---|
| `access_control_sop` allowlist | baseline cleaned không có `access_control_sop`; 8 dòng bị `unknown_doc_id` | `final-pass` cleaned có 6 dòng `access_control_sop`; `gq_d10_10` pass top1 | `artifacts/cleaned/cleaned_final-pass.csv`, `grading_run.jsonl` |
| `stale_hr_policy_text` | baseline còn 2 violations HR trong expectation | `final-pass` quarantine thêm 6 dòng `stale_hr_policy_text`; HR expectation pass | `artifacts/quarantine/quarantine_final-pass.csv` |
| `invalid_exported_at` | timestamp export sai format có thể vào cleaned | `final-pass` quarantine 7 dòng `invalid_exported_at`; `exported_at_iso_datetime` pass | `run_final-pass.log` |
| `ambiguous_chunk_text` | chunk “Nội dung không rõ ràng” có thể vào cleaned | `final-pass` quarantine 5 dòng `ambiguous_chunk_text`; warning `no_ambiguous_chunk_text` pass | `quarantine_final-pass.csv` |
| `required_grading_doc_coverage` | baseline thiếu `access_control_sop` | `final-pass` `missing_doc_ids=[]` | `run_final-pass.log` |
| `refund_no_stale_14d_window` | inject bad fail 2 violations | clean run pass 0 violations | `run_inject-bad.log`, `run_final-pass.log` |

## 3. Before / After Retrieval

Kịch bản inject:

```powershell
python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate
python eval_retrieval.py --out artifacts/eval/eval_after_inject_bad.csv
```

Inject cố ý giữ chunk refund 14 ngày và bỏ qua validation để publish index xấu. Trong `run_inject-bad.log`, expectation `refund_no_stale_14d_window` fail với 2 violations. File `artifacts/eval/eval_after_inject_bad.csv` có `q_refund_window contains_expected=no` và `hits_forbidden=yes`; `artifacts/eval/grading_after_inject_bad.jsonl` có `gq_d10_01 hits_forbidden=true`.

Sau khi chạy lại pipeline chuẩn, `artifacts/eval/eval_after_fix.csv` đạt 21/21: không fail contains, không hit forbidden, không fail top1. `artifacts/eval/grading_run.jsonl` đạt 10/10: `contains_expected=true`, `hits_forbidden=false`, và mọi câu có top1 đều `top1_doc_matches=true`.

## 4. Freshness & Monitoring

Manifest cuối `artifacts/manifests/manifest_final-pass.json` ghi `latest_exported_at=2026-04-11T00:00:00`. Vì chạy ngày 2026-06-10 với SLA 24 giờ, freshness check trả `FAIL` và reason `freshness_sla_exceeded`. Đây là cảnh báo đúng cho snapshot cũ; pipeline vẫn publish vì expectation dữ liệu sạch đã pass. Khi triển khai thật, freshness nên gửi alert `#data-quality` và block publish nếu source không được refresh theo SLA.

## 5. Liên Hệ Day 09

Day 09 multi-agent chỉ trả lời đúng nếu retrieval đọc đúng version tài liệu. Day 10 đảm bảo tầng dữ liệu trước agent: refund không còn 14 ngày, HR không còn bản 2025, và access-control được đưa vào index. Index `day10_kb` có thể dùng làm nguồn sạch cho retrieval worker trong Day 09.

## 6. Rủi Ro Còn Lại & Việc Chưa Làm

- Chroma chưa bật mặc định vì môi trường local import dependency chậm; local index là fallback ổn định cho grading.
- Các nguồn `security_policy` và `data_privacy_guideline` vẫn bị quarantine vì chưa có yêu cầu canonical trong grading.
- Freshness mới đo publish manifest; nên thêm đo boundary ingest và alert tự động nếu có thêm thời gian.
