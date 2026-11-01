from __future__ import annotations

import csv
import json
from pathlib import Path, PurePosixPath

import pandas as pd

from src.data.loader import FIELDS, stable_id


def validate_mapping(stage_dir: Path) -> list[dict]:
    """只接受官方 CSV 映射，不猜测图片与 JSON 的对应关系。"""
    mapping = stage_dir / "image_json_mapping.csv"
    if not mapping.is_file():
        raise FileNotFoundError(f"缺少官方映射文件：{mapping}")
    with mapping.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    required = {"image", "json", "match_type"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"映射 CSV 必须包含 {sorted(required)}")
    return rows


def import_stage(stage_dir: Path, stage_name: str) -> pd.DataFrame:
    """按 CSV 一行一图导入；step_2 共享 JSON 也保留为不同图片记录。"""
    output = []
    for mapping in validate_mapping(stage_dir):
        image_rel, json_rel = mapping["image"], mapping["json"]
        ann_path = stage_dir / "dataset_json" / PurePosixPath(json_rel)
        image_path = stage_dir / "dataset_image" / PurePosixPath(image_rel)
        if not ann_path.is_file():
            continue
        payload = json.loads(ann_path.read_text(encoding="utf-8"))
        record = next(iter(payload.values()), {})
        regions = record.get("regions") or []
        attrs = (regions[0].get("region_attributes", {}) if regions else {})
        vals = list(attrs.values())
        # 字段名保持原文，不能猜字段时只安全使用路径分类。
        path_parts = PurePosixPath(image_rel).parts
        name = path_parts[-2] if len(path_parts) > 1 else Path(image_rel).stem
        row = {c: "" for c in FIELDS}
        row.update({
            "pattern_id": stable_id(f"hf-{stage_name}", image_rel), "name": name,
            "category": path_parts[0] if path_parts else "", "image_path": str(image_path.resolve()) if image_path.is_file() else "",
            "source_name": "Traditional Pattern Dataset", "source_url": "https://huggingface.co/datasets/BaoWenwen/Traditional-Pattern-Dataset",
            "license": "CC BY-NC 4.0", "source_record_id": str(attrs.get("编号", "")),
            "source_file_path": str(ann_path.resolve()), "visual_keywords": [], "related_patterns": [],
            "summary": "", "evidence_status": "数据集标注，尚未独立核验",
        })
        output.append(row)
    return pd.DataFrame(output, columns=FIELDS)

