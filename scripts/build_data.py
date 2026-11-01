from __future__ import annotations

import json
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import project_path
from src.data.loader import audit_patterns, load_patterns, save_processed
from src.ontology import PatternGraph
from src.vision import analyze_features, feature_frame


def main() -> None:
    parser = argparse.ArgumentParser(description="重建正式纹样索引和审计产物")
    parser.add_argument("--output-dir", type=Path, default=None, help="可选输出目录；用于无损验证时不要写入正式 processed 目录")
    args = parser.parse_args()
    # 始终从原始元数据重建，避免沿用旧 CSV 中过期的图片可用状态。
    df = load_patterns(prefer_processed=False)
    if df.empty:
        raise SystemExit("没有找到正式数据。请将 Wényàng patterns.json 放入 data/raw/wenyang/data/。")
    output_dir = args.output_dir or project_path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    target = save_processed(df, output_dir / "patterns.csv")
    graph = PatternGraph(df)
    graph_path = output_dir / "pattern_graph.ttl"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph.graph.serialize(graph_path, format="turtle")
    feature_path = output_dir / "visual_features.npz"
    feature_index, feature_vectors = feature_frame(df, feature_path)
    visual_report = {"samples": int(len(feature_index)), "feature_method": "RGB histogram + RGB mean/std + HSV mean", "pca_components": 2, "kmeans_clusters": None, "silhouette": None, "cluster_counts": {}}
    if len(feature_index) >= 2:
        requested_clusters = 3
        analysis = analyze_features(feature_index, feature_vectors, requested_clusters)
        visual_report.update({"kmeans_clusters": int(analysis.cluster.nunique()), "silhouette": float(analysis.silhouette.iloc[0]) if analysis.silhouette.notna().any() else None, "cluster_counts": {str(k): int(v) for k, v in analysis.cluster.value_counts().sort_index().items()}})
    visual_path = output_dir / "visual_analysis.json"
    visual_path.write_text(json.dumps(visual_report, ensure_ascii=False, indent=2), encoding="utf-8")
    audit_path = output_dir / "audit.json"
    audit_path.write_text(json.dumps(audit_patterns(df), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {target}: {len(df)} 条；图谱 {len(graph.graph)} triples；视觉样本 {len(feature_index)}；审计 {audit_path}")


if __name__ == "__main__":
    main()
