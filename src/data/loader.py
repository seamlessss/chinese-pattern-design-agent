from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import ROOT, load_config, project_path

FIELDS = [
    "pattern_id", "name", "name_en", "category", "historical_period",
    "cultural_meaning", "application_context", "visual_keywords", "summary",
    "image_path", "source_name", "source_url", "license", "source_record_id",
    "source_file_path", "detail_path", "related_patterns", "evidence_status",
    "evidence_type", "external_evidence_status",
]


def _list_value(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            return [str(x) for x in ast.literal_eval(text)]
        except (ValueError, SyntaxError):
            pass
    normalized = text.replace("，", ",").replace("、", ",")
    return [x.strip() for x in normalized.split(",") if x.strip()]


def _detail_sections(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE))
    sections = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        sections[match.group(1).strip()] = body
    return sections


def normalize_wenyang(raw: list[dict], raw_root: Path) -> pd.DataFrame:
    """把 Wényàng 实际 JSON 字段映射到统一模型；不存在的事实保持为空。"""
    cfg = load_config()["source"]
    preview_dir = raw_root / "docs" / "preview"
    rows: list[dict] = []
    for item in raw:
        source_id = str(item.get("id", "")).strip()
        card = raw_root / str(item.get("card_image", ""))
        preview = preview_dir / f"{source_id}.jpg"
        image = card if card.is_file() else preview if preview.is_file() else None
        summary = str(item.get("summary", "")).strip()
        detail = raw_root / str(item.get("detail_page", ""))
        sections = _detail_sections(detail)
        carrier_text = sections.get("常见载体", "").strip().rstrip("。")
        carriers = _list_value(carrier_text) if carrier_text else [x for x in ("瓷器", "陶瓷", "织锦", "织绣", "建筑", "漆器", "家具", "服饰", "器物") if x in summary]
        related_names = _list_value(sections.get("关联纹样", "").strip().rstrip("。"))
        rows.append({
            "pattern_id": f"wenyang:{source_id}",
            "name": str(item.get("name_cn", "")).strip(),
            "name_en": str(item.get("name_en", "")).strip(),
            "category": str(item.get("category", "")).strip(),
            "historical_period": "",
            "cultural_meaning": str(item.get("meaning", "")).strip(),
            "application_context": "、".join(carriers),
            "visual_keywords": _list_value(item.get("visual_keywords")),
            "summary": summary,
            "image_path": str(image.resolve()) if image else "",
            "source_name": cfg["name"], "source_url": cfg["url"],
            "license": cfg["license"], "source_record_id": source_id,
            "source_file_path": str((raw_root / "data" / "patterns.json").resolve()),
            "detail_path": str(detail.resolve()),
            "related_patterns": related_names,
            "evidence_status": "数据集描述，尚未独立核验",
            "evidence_type": "dataset_description",
            "external_evidence_status": "not_available",
        })
    name_to_id = {row["name"]: row["pattern_id"] for row in rows}
    for row in rows:
        row["related_patterns"] = [name_to_id[name] for name in row["related_patterns"] if name in name_to_id and name != row["name"]]
    return pd.DataFrame(rows, columns=FIELDS)


def load_patterns(path: Path | None = None, *, prefer_processed: bool = True) -> pd.DataFrame:
    cfg = load_config()["paths"]
    processed = project_path(path or cfg["processed_csv"])
    if prefer_processed and processed.is_file():
        df = pd.read_csv(processed, keep_default_na=False)
        for col in ("visual_keywords", "related_patterns"):
            if col in df:
                df[col] = df[col].map(_list_value)
        return df.reindex(columns=FIELDS, fill_value="")
    raw_path = project_path(cfg["wenyang_json"])
    if not raw_path.is_file():
        return pd.DataFrame(columns=FIELDS)
    with raw_path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return normalize_wenyang(raw, raw_path.parents[1])


def save_processed(df: pd.DataFrame, path: Path | None = None) -> Path:
    target = path or project_path(load_config()["paths"]["processed_csv"])
    target.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    for col in ("visual_keywords", "related_patterns"):
        out[col] = out[col].map(lambda x: json.dumps(_list_value(x), ensure_ascii=False))
    out.to_csv(target, index=False, encoding="utf-8-sig")
    return target


def audit_patterns(df: pd.DataFrame) -> dict:
    missing_images = int(sum(not (p and Path(p).is_file()) for p in df.get("image_path", [])))
    coverage = {}
    for column in FIELDS:
        if not len(df):
            coverage[column] = 0
        elif column in ("visual_keywords", "related_patterns"):
            coverage[column] = round(float(df[column].map(lambda value: bool(_list_value(value))).mean()), 4)
        else:
            coverage[column] = round(float(df[column].astype(str).str.strip().ne("").mean()), 4)
    return {
        "records": int(len(df)), "available_images": int(len(df) - missing_images),
        "missing_images": missing_images,
        "duplicate_ids": int(df["pattern_id"].duplicated().sum()) if len(df) else 0,
        "sources": df["source_name"].value_counts().to_dict() if len(df) else {},
        "field_coverage": coverage,
    }


def stable_id(source: str, relative_path: str) -> str:
    return f"{source}:{hashlib.sha1(relative_path.encode('utf-8')).hexdigest()[:16]}"
