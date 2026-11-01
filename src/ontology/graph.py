from __future__ import annotations

from collections import Counter
from urllib.parse import quote

import pandas as pd
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef

EX = Namespace("https://example.org/traditional-pattern/")


def _uri(kind: str, value: str) -> URIRef:
    return EX[f"{kind}/{quote(str(value), safe='')}"]


class PatternGraph:
    classes = ["Pattern", "HistoricalPeriod", "MotifCategory", "CulturalMeaning", "ApplicationContext", "VisualFeature", "Source"]
    relations = {"historical_period": "hasPeriod", "category": "hasCategory", "cultural_meaning": "hasMeaning", "application_context": "suitableFor", "source_name": "supportedBySource"}

    def __init__(self, frame: pd.DataFrame | None = None):
        self.graph = Graph()
        self.graph.bind("pattern", EX)
        for cls in self.classes:
            self.graph.add((EX[cls], RDF.type, RDFS.Class))
        for rel in [*self.relations.values(), "hasVisualFeature", "relatedTo"]:
            self.graph.add((EX[rel], RDF.type, RDF.Property))
        if frame is not None:
            self.build(frame)

    def build(self, frame: pd.DataFrame) -> Graph:
        for _, row in frame.iterrows():
            pid = str(row.get("pattern_id", ""))
            if not pid:
                continue
            subject = _uri("pattern", pid)
            self.graph.add((subject, RDF.type, EX.Pattern))
            self.graph.add((subject, RDFS.label, Literal(str(row.get("name", "")), lang="zh")))
            for field, predicate in self.relations.items():
                value = str(row.get(field, "")).strip()
                if value:
                    kind = {"historical_period":"period", "category":"category", "cultural_meaning":"meaning", "application_context":"context", "source_name":"source"}[field]
                    entity_class = {"historical_period":"HistoricalPeriod", "category":"MotifCategory", "cultural_meaning":"CulturalMeaning", "application_context":"ApplicationContext", "source_name":"Source"}[field]
                    obj = _uri(kind, value)
                    self.graph.add((subject, EX[predicate], obj))
                    self.graph.add((obj, RDF.type, EX[entity_class]))
                    self.graph.add((obj, RDFS.label, Literal(value, lang="zh")))
            for keyword in row.get("visual_keywords", []) or []:
                obj = _uri("feature", keyword)
                self.graph.add((subject, EX.hasVisualFeature, obj)); self.graph.add((obj, RDF.type, EX.VisualFeature)); self.graph.add((obj, RDFS.label, Literal(keyword, lang="zh")))
            for related in row.get("related_patterns", []) or []:
                self.graph.add((subject, EX.relatedTo, _uri("pattern", related)))
        return self.graph

    def find(self, name: str) -> list[dict]:
        results = []
        for subject in self.graph.subjects(RDFS.label, Literal(name, lang="zh")):
            for predicate, obj in self.graph.predicate_objects(subject):
                if predicate in (RDF.type, RDFS.label):
                    continue
                label = next(self.graph.objects(obj, RDFS.label), obj)
                results.append({"relation": self.label(predicate), "value": str(label)})
        return results

    def patterns_by(self, relation: str, value: str) -> list[str]:
        predicate = EX[relation]
        names = []
        for subject, obj in self.graph.subject_objects(predicate):
            label = str(next(self.graph.objects(obj, RDFS.label), ""))
            if value.lower() in label.lower():
                names.append(str(next(self.graph.objects(subject, RDFS.label), subject)))
        return names

    def related(self, pattern_id: str) -> list[str]:
        subject = _uri("pattern", pattern_id)
        return [str(next(self.graph.objects(obj, RDFS.label), obj)) for obj in self.graph.objects(subject, EX.relatedTo)]

    @staticmethod
    def label(uri: URIRef) -> str:
        return str(uri).rsplit("/", 1)[-1]

    def stats(self) -> dict:
        types = Counter(self.label(o) for _, _, o in self.graph.triples((None, RDF.type, None)) if o in [EX[c] for c in self.classes])
        rels = Counter(self.label(p) for _, p, _ in self.graph if p not in (RDF.type, RDFS.label))
        return {"triples": len(self.graph), "entities": len(set(self.graph.subjects()) | set(self.graph.objects())), "entity_types": dict(types), "relation_types": dict(rels)}
