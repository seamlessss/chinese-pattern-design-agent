from __future__ import annotations

import hashlib
import html

from .prompts import validate_design_input


def generate_programmatic_svg(theme: str, style: str, palette: list[str], scene: str, requirements: str = "") -> bytes:
    """Create an original, deterministic SVG repeat tile; this is not an AI model output."""
    design = validate_design_input(theme, style, palette, scene, requirements)
    colors = design["palette"]
    seed = int(hashlib.sha256(design["theme"].encode("utf-8")).hexdigest()[:8], 16)
    rotation = seed % 60 - 30
    accent = colors[1] if len(colors) > 1 else colors[0]
    secondary = colors[2] if len(colors) > 2 else colors[0]
    label = html.escape(design["theme"])
    petal = (
        "M0 -53 C38 -24 38 24 0 53 C-38 24 -38 -24 0 -53Z"
        if design["style"] != "现代简约"
        else "M0 -48 L34 0 L0 48 L-34 0Z"
    )
    frame = '<rect x="-54" y="-54" width="108" height="108" fill="none" stroke="%s" stroke-width="3" transform="rotate(45)"/>' % colors[0] if design["style"] == "新中式" else ""
    motif = (
        f'<g transform="translate(90 90) rotate({rotation})">'
        f'{frame}<path d="{petal}" fill="none" stroke="{accent}" stroke-width="5"/>'
        f'<path d="M-43 0 C-18 -19 18 -19 43 0 C18 19 -18 19 -43 0Z" fill="none" stroke="{colors[0]}" stroke-width="4"/>'
        f'<circle cx="0" cy="0" r="12" fill="{secondary}"/>'
        f'<circle cx="0" cy="-67" r="4" fill="{accent}"/><circle cx="67" cy="0" r="4" fill="{accent}"/>'
        f'<circle cx="0" cy="67" r="4" fill="{accent}"/><circle cx="-67" cy="0" r="4" fill="{accent}"/>'
        '</g>'
    )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="360" viewBox="0 0 720 360" role="img">'
        f'<title>程序化生成纹样：{label} · {html.escape(design["scene"])}</title><rect width="720" height="360" fill="#FAF8F2"/>'
        f'<defs><pattern id="repeat" width="180" height="180" patternUnits="userSpaceOnUse">'
        f'<rect width="180" height="180" fill="#FAF8F2"/><path d="M0 90H180 M90 0V180" stroke="{colors[0]}" stroke-opacity=".16" stroke-width="1.5"/>'
        f'{motif}</pattern></defs><rect width="720" height="360" fill="url(#repeat)"/></svg>'
    )
    return svg.encode("utf-8")
