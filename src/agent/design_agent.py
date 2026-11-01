from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.ontology import PatternGraph
from src.retrieval import TextRetriever
from src.vision import visual_neighbors

PERIODS = ["先秦", "商", "周", "汉", "魏晋", "唐", "宋", "元", "明", "清", "现代"]
CARRIERS = ["茶具", "文房", "瓷器", "陶瓷", "织锦", "服饰", "建筑", "家具", "漆器", "包装"]
MEANINGS = ["吉祥", "长寿", "富贵", "圆满", "清雅", "和谐", "繁荣", "生生不息", "幸福"]
VISUAL = ["简洁", "雅致", "对称", "几何", "连续", "华丽", "柔和", "素雅"]


def parse_design_request(text: str, categories: list[str] | None = None) -> dict:
    def hits(words): return [x for x in words if x in text]
    periods = [x for x in PERIODS if (x in text if len(x) > 1 else re.search(re.escape(x) + r"(?:代|朝|风格|式)", text))]
    return {"raw": text, "periods": periods, "contexts": hits(CARRIERS), "meanings": hits(MEANINGS), "categories": hits(categories or []), "visual_keywords": hits(VISUAL), "color_preferences": hits(["蓝", "青", "红", "金", "黑", "白", "绿"])}


class DesignAgent:
    def __init__(self, frame: pd.DataFrame, graph: PatternGraph, retriever: TextRetriever, vision_index: pd.DataFrame | None = None, vision_vectors: np.ndarray | None = None, weights: dict | None = None):
        self.frame, self.graph, self.retriever = frame.copy(), graph, retriever
        self.vision_index = vision_index if vision_index is not None else pd.DataFrame()
        self.vision_vectors = vision_vectors if vision_vectors is not None else np.array([])
        self.weights = weights or {"structured": .55, "text": .30, "visual": .15}

    def search_patterns(self, needs: dict) -> pd.DataFrame:
        """宽召回：只对有明确结构化字段的条件筛选，未知字段不算命中。"""
        df = self.frame.copy()
        if needs["categories"]:
            df = df[df.category.map(lambda x: any(v in str(x) for v in needs["categories"]))]
        return df

    def query_knowledge_graph(self, needs: dict) -> dict:
        answer = {}
        for value in needs["categories"]:
            answer[value] = self.graph.patterns_by("hasCategory", value)
        for value in needs["meanings"]:
            answer[value] = self.graph.patterns_by("hasMeaning", value)
        return answer

    def retrieve_cultural_evidence(self, request: str, candidate_ids: set[str]) -> list[dict]:
        return self.retriever.search(request, top_k=max(5, len(candidate_ids)), pattern_ids=candidate_ids)

    def find_visual_neighbors(self, query_image, top_k: int = 5) -> list[dict]:
        return visual_neighbors(query_image, self.vision_index, self.vision_vectors, top_k) if query_image is not None else []

    def rank_candidates(self, candidates: pd.DataFrame, needs: dict, evidence: list[dict], visual: list[dict]) -> list[dict]:
        evidence_scores = {}
        evidence_best = {}
        for e in evidence:
            if e["score"] >= evidence_scores.get(e["pattern_id"], -1):
                evidence_scores[e["pattern_id"]] = e["score"]
                evidence_best[e["pattern_id"]] = e
        visual_scores = {v["pattern_id"]: v["similarity"] for v in visual}
        ranked = []
        for _, row in candidates.iterrows():
            checks = [
                (term, "历史时期", str(row.get("historical_period", ""))) for term in needs["periods"]
            ] + [
                (term, "使用场景", str(row.get("application_context", ""))) for term in needs["contexts"]
            ] + [
                (term, "文化寓意", str(row.get("cultural_meaning", ""))) for term in needs["meanings"]
            ] + [
                (term, "纹样类别", str(row.get("category", ""))) for term in needs["categories"]
            ] + [
                (term, "视觉特征", " ".join(row.get("visual_keywords", []) or [])) for term in needs["visual_keywords"]
            ] + [
                (term, "颜色偏好", " ".join(row.get("visual_keywords", []) or [])) for term in needs["color_preferences"]
            ]
            # 同一个词只计算一次，同时保留其匹配维度用于解释。
            unique_checks = []
            seen = set()
            for term, dimension, value in checks:
                if term not in seen:
                    unique_checks.append((term, dimension, value)); seen.add(term)
            matched = [f"{dimension}={term}" for term, dimension, value in unique_checks if value.strip() and term in value]
            unmatched = [f"{dimension}={term}" for term, dimension, value in unique_checks if not value.strip() or term not in value]
            explicit = unique_checks
            structured = len(matched) / len(explicit) if explicit else 0.5
            text = float(evidence_scores.get(row["pattern_id"], 0))
            vision = float(visual_scores.get(row["pattern_id"], 0))
            total = self.weights["structured"] * structured + self.weights["text"] * text + self.weights["visual"] * vision
            completeness_fields = ["name", "category", "historical_period", "cultural_meaning", "application_context", "visual_keywords", "image_path"]
            completeness = sum(bool(row.get(k, "")) for k in completeness_fields) / len(completeness_fields)
            reasons = ([f"明确匹配：{'、'.join(matched)}"] if matched else ["由文本资料相关性进入候选"]) + ([f"TF-IDF 证据相关度 {text:.2f}"] if text else []) + ([f"颜色特征相似度 {vision:.2f}"] if vision else [])
            risks = []
            period = str(row.get("historical_period", "")).strip()
            if needs["periods"] and not period: risks.append("来源未提供时代，目标时期需另行核验")
            elif needs["periods"] and not any(term in period for term in needs["periods"]): risks.append(f"目标时期与记录时期不一致（记录：{period}）")
            if needs["contexts"] and not str(row.get("application_context", "")).strip(): risks.append("载体资料缺失")
            if not str(row.get("cultural_meaning", "")).strip(): risks.append("寓意资料不足")
            ranked.append({**row.to_dict(), "score": total, "structured_score": structured, "text_score": text, "visual_score": vision, "matched": matched, "unmatched": unmatched, "reasons": reasons, "risks": risks, "completeness": completeness, "evidence": evidence_best.get(row["pattern_id"]), "evidence_type": row.get("evidence_type", "dataset_description"), "external_evidence_status": row.get("external_evidence_status", "not_available")})
        return sorted(ranked, key=lambda x: (-x["score"], x["pattern_id"]))

    def run(self, request: str, query_image=None, top_k: int = 5) -> dict:
        trace = []
        needs = parse_design_request(request, sorted(self.frame.category.dropna().unique().tolist()))
        trace.append({"tool": "parse_design_request", "result": needs})
        candidates = self.search_patterns(needs); trace.append({"tool": "search_patterns", "count": len(candidates)})
        kg = self.query_knowledge_graph(needs); trace.append({"tool": "query_knowledge_graph", "relations": sum(len(v) for v in kg.values())})
        if candidates.empty:
            return {"needs": needs, "candidates": [], "evidence": [], "trace": trace, "message": "没有候选符合明确的结构化条件，请放宽类别等条件。"}
        evidence = self.retrieve_cultural_evidence(request, set(candidates.pattern_id)); trace.append({"tool": "retrieve_cultural_evidence", "count": len(evidence)})
        visual = self.find_visual_neighbors(query_image, top_k) if query_image is not None else []; trace.append({"tool": "find_visual_neighbors", "count": len(visual), "method": "RGB 直方图与颜色统计"})
        ranked = self.rank_candidates(candidates, needs, evidence, visual)[:top_k]; trace.append({"tool": "rank_candidates", "count": len(ranked), "weights": self.weights})
        return {"needs": needs, "candidates": ranked, "evidence": evidence, "trace": trace, "message": ""}
