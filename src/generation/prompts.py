from __future__ import annotations

import re

ALLOWED_STYLES = {"传统装饰", "现代简约", "新中式"}
ALLOWED_SCENES = {"茶具", "织物", "包装", "文房器物", "家居装饰", "自由应用"}
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def validate_design_input(theme: str, style: str, palette: list[str], scene: str, requirements: str = "") -> dict:
    theme = " ".join((theme or "").split())
    requirements = " ".join((requirements or "").split())
    if not 2 <= len(theme) <= 80:
        raise ValueError("主题请填写 2–80 个字符。")
    if style not in ALLOWED_STYLES:
        raise ValueError("请选择有效的设计风格。")
    if scene not in ALLOWED_SCENES:
        raise ValueError("请选择有效的应用场景。")
    if not palette or len(palette) > 5 or any(not HEX_RE.fullmatch(color) for color in palette):
        raise ValueError("请选择 1–5 个有效的十六进制配色。")
    if len(requirements) > 500:
        raise ValueError("补充要求最多 500 个字符。")
    return {"theme": theme, "style": style, "palette": [c.upper() for c in palette], "scene": scene, "requirements": requirements}


def build_pattern_prompt(theme: str, style: str, palette: list[str], scene: str, requirements: str = "", reference: dict | None = None) -> tuple[str, dict]:
    design = validate_design_input(theme, style, palette, scene, requirements)
    reference_info = None
    reference_lines = ""
    if reference:
        keywords = reference.get("visual_keywords", [])
        if isinstance(keywords, str):
            keywords = [part.strip() for part in re.split(r"[,，、]", keywords) if part.strip()]
        summary = " ".join(str(reference.get("summary", "")).split())[:240]
        name = " ".join(str(reference.get("name", "")).split())[:80]
        reference_info = {
            "pattern_id": str(reference.get("pattern_id", "")),
            "name": name,
            "source_name": str(reference.get("source_name", "")),
            "source_url": str(reference.get("source_url", "")),
            "license": str(reference.get("license", "")),
            "historical_period": str(reference.get("historical_period", "")).strip(),
        }
        reference_lines = (
            f"Reference motif name: {name or 'not provided'}.\n"
            f"Dataset visual keywords (unverified dataset description): {', '.join(map(str, keywords[:12])) or 'not provided'}.\n"
            f"Dataset summary (unverified; use only as design inspiration): {summary or 'not provided'}.\n"
            f"Reference source: {reference_info['source_url'] or 'not provided'}; record ID: {reference_info['pattern_id'] or 'not provided'}.\n"
        )
        if reference_info["historical_period"]:
            reference_lines += f"Recorded period: {reference_info['historical_period']} (source field; do not imply independent verification).\n"
        else:
            reference_lines += "Historical period: not provided and not verified; do not assign a period.\n"

    prompt = (
        "Create one original decorative Chinese-inspired repeating motif as a clean, flat, high-resolution design sheet. "
        "Do not reproduce an existing image or claim historical authenticity. No text, labels, seals, signatures, watermark, "
        "mockup, photographed artifact, or 3D product render. Use a clear centered repeat tile with crisp edges and visible negative space.\n"
        f"Theme: {design['theme']}. Style direction: {design['style']}. Intended application: {design['scene']}.\n"
        f"Palette (hex): {', '.join(design['palette'])}. Additional user requirements: {design['requirements'] or 'none'}.\n"
        f"{reference_lines}"
        "Reference descriptions are dataset text, not independently verified historical facts. Produce a new visual interpretation only; "
        "do not infer a dynasty, cultural meaning, or provenance."
    )
    if len(prompt) > 4000:
        raise ValueError("组合后的提示词超过 4000 个字符，请缩短输入。")
    return prompt, {**design, "reference": reference_info}

