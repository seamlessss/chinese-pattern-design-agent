from src.ontology import PatternGraph


def test_graph_generated_from_data(sample_frame):
    graph=PatternGraph(sample_frame)
    assert graph.stats()["relation_types"]["hasCategory"]==3
    assert graph.stats()["entity_types"]["MotifCategory"]==3
    assert any(x["value"]=="植物纹" for x in graph.find("莲纹"))


def test_graph_filters_and_omits_unknown_period(sample_frame):
    graph=PatternGraph(sample_frame)
    assert graph.patterns_by("hasMeaning","清雅")==["莲纹"]
    assert "hasPeriod" not in graph.stats()["relation_types"]
