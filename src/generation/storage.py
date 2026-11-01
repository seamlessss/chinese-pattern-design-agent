from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .providers import GenerationResult


def save_generation(result: GenerationResult, prompt: str, parameters: dict, output_dir: Path) -> dict:
    if result.mime_type not in {"image/png", "image/svg+xml"} or not result.image_bytes:
        raise ValueError("生成结果缺少有效图片内容或格式不受支持。")
    extension = {"image/png": ".png", "image/svg+xml": ".svg"}[result.mime_type]
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_id = uuid.uuid4().hex
    image_path = output_dir / f"{artifact_id}{extension}"
    metadata_path = output_dir / f"{artifact_id}.json"
    image_path.write_bytes(result.image_bytes)
    metadata = {
        "artifact_id": artifact_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "程序化生成" if result.provider == "Programmatic SVG" else "AI 生成",
        "provider": result.provider,
        "model": result.model,
        "size": result.size,
        "quality": result.quality if result.provider != "Programmatic SVG" else "not_applicable",
        "mime_type": result.mime_type,
        "prompt": prompt,
        "parameters": parameters,
        "reference_pattern_id": (parameters.get("reference") or {}).get("pattern_id"),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**metadata, "image_path": str(image_path), "metadata_path": str(metadata_path), "image_bytes": result.image_bytes}
