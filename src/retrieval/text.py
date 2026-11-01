from __future__ import annotations

import numpy as np
import pandas as pd
import re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer


class TextRetriever:
    def __init__(self, frame: pd.DataFrame):
        self.documents: list[dict] = []
        for _, row in frame.iterrows():
            chunks = [("数据集摘要", str(row.get("summary", ""))), ("数据集寓意", str(row.get("cultural_meaning", "")))]
            detail_path = Path(str(row.get("detail_path", "")))
            if detail_path.is_file():
                detail = detail_path.read_text(encoding="utf-8")
                matches = list(re.finditer(r"^##\s+(.+?)\s*$", detail, flags=re.MULTILINE))
                allowed = {"纹样构成", "视觉特征", "文化寓意", "常见载体", "色彩建议", "现代应用", "素材说明"}
                for index, match in enumerate(matches):
                    title = match.group(1).strip()
                    if title not in allowed:
                        continue
                    end = matches[index + 1].start() if index + 1 < len(matches) else len(detail)
                    body = detail[match.end():end].strip()
                    if body:
                        chunks.append((f"详情页·{title}", body))
            for title, text in chunks:
                if text.strip():
                    source_path = str(detail_path) if title.startswith("详情页·") else row["source_file_path"]
                    self.documents.append({"pattern_id": row["pattern_id"], "name": row["name"], "title": title, "text": text, "source": row["source_url"], "source_path": source_path, "evidence_status": row["evidence_status"], "evidence_type": row.get("evidence_type", "dataset_description"), "external_evidence_status": row.get("external_evidence_status", "not_available")})
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(1, 3), min_df=1)
        self.matrix = self.vectorizer.fit_transform([d["text"] + d["name"] for d in self.documents]) if self.documents else None

    def search(self, query: str, top_k: int = 5, pattern_ids: set[str] | None = None) -> list[dict]:
        if self.matrix is None or not query.strip():
            return []
        scores = (self.matrix @ self.vectorizer.transform([query]).T).toarray().ravel()
        order = np.argsort(scores)[::-1]
        results = []
        for idx in order:
            doc = self.documents[int(idx)]
            if scores[idx] <= 0 or (pattern_ids is not None and doc["pattern_id"] not in pattern_ids):
                continue
            results.append({**doc, "score": float(scores[idx])})
            if len(results) >= top_k:
                break
        return results

    def answer(self, query: str, top_k: int = 3) -> dict:
        hits = self.search(query, top_k)
        if not hits:
            return {"answer": "现有资料不足以确认。", "evidence": []}
        lines = [f"据现有数据集资料，{h['name']}：{h['text']}" for h in hits]
        return {"answer": "\n".join(lines) + "\n\n证据类型：数据集自身描述；当前没有外部资料交叉核验，不应视为独立历史事实。", "evidence": hits}
