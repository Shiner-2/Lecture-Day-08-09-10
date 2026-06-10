from __future__ import annotations

import csv
import json
import math
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parent
LOCAL_INDEX_DIR = ROOT / "artifacts" / "local_index"

STOPWORDS = {
    "ai",
    "bao",
    "bi",
    "boi",
    "cai",
    "can",
    "cho",
    "co",
    "cua",
    "duoc",
    "gi",
    "hien",
    "khi",
    "la",
    "lam",
    "muc",
    "nao",
    "neu",
    "sau",
    "theo",
    "thi",
    "trong",
    "tu",
    "va",
    "ve",
    "voi",
    "yeu",
}


def _strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _normalize(text: str) -> str:
    return _strip_accents(text or "").lower()


def _tokens(text: str) -> List[str]:
    toks = re.findall(r"[a-z0-9#@.-]+", _normalize(text))
    return [t for t in toks if len(t) > 1 and t not in STOPWORDS]


def _local_index_path(collection_name: str | None = None) -> Path:
    name = collection_name or os.environ.get("CHROMA_COLLECTION", "day10_kb")
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", name)
    return LOCAL_INDEX_DIR / f"{safe}.json"


def load_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def publish_local_index(cleaned_csv: Path, *, run_id: str, collection_name: str | None = None) -> Path:
    rows = load_csv_rows(cleaned_csv)
    LOCAL_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    out = _local_index_path(collection_name)
    payload = {
        "run_id": run_id,
        "rows": rows,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def load_local_index(collection_name: str | None = None) -> List[Dict[str, str]]:
    path = _local_index_path(collection_name)
    if not path.is_file():
        raise FileNotFoundError(f"local index not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("rows") or [])


def _score(query: str, row: Dict[str, Any]) -> float:
    q_norm = _normalize(query)
    doc = f"{row.get('doc_id', '')} {row.get('chunk_text', '')}"
    d_norm = _normalize(doc)
    q_tokens = _tokens(query)
    d_tokens = _tokens(doc)
    if not q_tokens or not d_tokens:
        return 0.0

    d_counts: Dict[str, int] = {}
    for tok in d_tokens:
        d_counts[tok] = d_counts.get(tok, 0) + 1

    overlap = sum(min(2, d_counts.get(tok, 0)) for tok in q_tokens)
    coverage = len({tok for tok in q_tokens if tok in d_counts}) / max(1, len(set(q_tokens)))
    phrase_boost = 0.0
    for n in (4, 3, 2):
        for i in range(0, max(0, len(q_tokens) - n + 1)):
            phrase = " ".join(q_tokens[i : i + n])
            if phrase in d_norm:
                phrase_boost += n * 0.7

    entity_boost = 0.0
    route_terms = {
        "policy_refund_v4": ("hoan tien", "refund", "finance", "don hang"),
        "sla_p1_2026": ("p1", "sla", "ticket", "escalate", "resolution"),
        "it_helpdesk_faq": ("mat khau", "vpn", "tai khoan", "email", "helpdesk"),
        "hr_leave_policy": ("phep nam", "nghi om", "nhan vien", "kinh nghiem", "hr"),
        "access_control_sop": ("access", "quyen", "level", "admin", "ciso", "standard"),
    }
    doc_id = str(row.get("doc_id") or "")
    for term in route_terms.get(doc_id, ()):
        if term in q_norm:
            entity_boost += 1.6
    for term in ("standard access", "level 4", "admin access", "read only", "elevated access"):
        if term in q_norm and term in d_norm:
            entity_boost += 5.0

    length_penalty = math.log(len(d_tokens) + 8, 10)
    return (overlap + phrase_boost) / length_penalty + coverage * 4.0 + entity_boost


def local_query(query: str, *, top_k: int = 5, collection_name: str | None = None) -> List[Dict[str, Any]]:
    rows = load_local_index(collection_name)
    ranked = []
    for pos, row in enumerate(rows):
        ranked.append((_score(query, row), -pos, row))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [row for score, _, row in ranked[:top_k] if score > 0]
