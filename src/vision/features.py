from __future__ import annotations

import colorsys
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, UnidentifiedImageError
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


def extract_features(image_or_path, bins: int = 8) -> dict:
    try:
        image = Image.open(image_or_path).convert("RGB").resize((128, 128))
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"无法读取图片：{exc}") from exc
    pixels = np.asarray(image, dtype=np.float32).reshape(-1, 3) / 255.0
    hist = np.concatenate([np.histogram(pixels[:, i], bins=bins, range=(0, 1), density=False)[0] for i in range(3)]).astype(float)
    hist /= max(hist.sum(), 1)
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in pixels[::16]])
    quantized = (pixels * 5).astype(int).clip(0, 4)
    codes = quantized @ np.array([25, 5, 1])
    counts = np.bincount(codes, minlength=125)
    top_codes = np.argsort(counts)[::-1][:5]
    palette = []
    for code in top_codes:
        rgb = np.array([code // 25, (code // 5) % 5, code % 5]) * 255 / 4
        palette.append("#" + "".join(f"{int(x):02X}" for x in rgb))
    return {"vector": np.r_[hist, pixels.mean(0), pixels.std(0), hsv.mean(0)], "dominant_hex": palette[0], "palette_hex": palette, "mean_rgb": pixels.mean(0).tolist()}


def _image_signature(frame: pd.DataFrame) -> str:
    parts = []
    for _, row in frame.iterrows():
        path = Path(str(row.get("image_path", "")))
        if path.is_file():
            stat = path.stat()
            parts.append(f"{row['pattern_id']}|{path}|{stat.st_size}|{stat.st_mtime_ns}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def feature_frame(frame: pd.DataFrame, cache_path: Path | None = None) -> tuple[pd.DataFrame, np.ndarray]:
    signature = _image_signature(frame)
    if cache_path is not None and cache_path.is_file():
        try:
            cached = np.load(cache_path, allow_pickle=False)
            if str(cached["signature"].item()) == signature:
                index = pd.DataFrame({key: cached[key].astype(str) for key in ("pattern_id", "name", "category", "dominant_hex")})
                return index, cached["vectors"]
        except (OSError, ValueError, KeyError):
            pass
    rows, vectors = [], []
    for _, row in frame.iterrows():
        path = str(row.get("image_path", ""))
        if not path or not Path(path).is_file():
            continue
        try:
            feat = extract_features(path)
        except ValueError:
            continue
        rows.append({"pattern_id": row["pattern_id"], "name": row["name"], "category": row["category"], "dominant_hex": feat["dominant_hex"]})
        vectors.append(feat["vector"])
    index, matrix = pd.DataFrame(rows), np.asarray(vectors)
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache_path, signature=np.array(signature), vectors=matrix,
            pattern_id=index.get("pattern_id", pd.Series(dtype=str)).astype(str).to_numpy(),
            name=index.get("name", pd.Series(dtype=str)).astype(str).to_numpy(),
            category=index.get("category", pd.Series(dtype=str)).astype(str).to_numpy(),
            dominant_hex=index.get("dominant_hex", pd.Series(dtype=str)).astype(str).to_numpy())
    return index, matrix


def visual_neighbors(query, index: pd.DataFrame, vectors: np.ndarray, top_k: int = 5, exclude_id: str | None = None) -> list[dict]:
    if vectors.size == 0:
        return []
    q = extract_features(query)["vector"]
    dist = np.linalg.norm(vectors - q, axis=1)
    scale = max(float(dist.max()), 1e-9)
    results = []
    for idx in np.argsort(dist):
        row = index.iloc[int(idx)].to_dict()
        if row["pattern_id"] == exclude_id:
            continue
        results.append({**row, "distance": float(dist[idx]), "similarity": float(1 - dist[idx] / scale)})
        if len(results) >= top_k:
            break
    return results


def analyze_features(index: pd.DataFrame, vectors: np.ndarray, clusters: int = 3) -> pd.DataFrame:
    out = index.copy()
    if len(out) < 2:
        return out.assign(pc1=np.nan, pc2=np.nan, cluster=-1, silhouette=np.nan)
    coords = PCA(n_components=2).fit_transform(vectors)
    k = min(max(2, clusters), len(out) - 1) if len(out) > 2 else 1
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(vectors) if k > 1 else np.zeros(len(out), dtype=int)
    score = silhouette_score(vectors, labels) if k > 1 and len(set(labels)) > 1 else np.nan
    return out.assign(pc1=coords[:, 0], pc2=coords[:, 1], cluster=labels, silhouette=score)
