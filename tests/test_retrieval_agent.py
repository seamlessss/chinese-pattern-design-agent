from src.agent import DesignAgent, parse_design_request
from src.ontology import PatternGraph
from src.retrieval import TextRetriever
from src.vision import feature_frame
import pandas as pd
from src.data.loader import FIELDS


def test_text_retrieval_returns_source(sample_frame):
    hits=TextRetriever(sample_frame).search("清雅莲花")
    assert hits and hits[0]["source"]=="local:test"
    assert hits[0]["evidence_type"]=="dataset_description" and hits[0]["external_evidence_status"]=="not_available"


def test_no_evidence_answer(sample_frame):
    answer=TextRetriever(sample_frame).answer("完全无关的XYZ")
    assert answer["answer"]=="现有资料不足以确认。"


def test_parse_only_explicit_needs():
    parsed=parse_design_request("宋代简洁清雅茶具")
    assert parsed["periods"]==["宋"] and parsed["contexts"]==["茶具"] and "华丽" not in parsed["visual_keywords"]


def test_agent_tool_chain_and_ranking(sample_frame):
    graph=PatternGraph(sample_frame); retriever=TextRetriever(sample_frame); index,vectors=feature_frame(sample_frame)
    result=DesignAgent(sample_frame,graph,retriever,index,vectors).run("想做简洁清雅的瓷器")
    tools=[x["tool"] for x in result["trace"]]
    assert tools==["parse_design_request","search_patterns","query_knowledge_graph","retrieve_cultural_evidence","find_visual_neighbors","rank_candidates"]
    assert result["candidates"][0]["name"]=="莲纹" and not any("宋" in x for x in result["candidates"][0]["matched"])


def test_agent_no_candidates():
    empty=pd.DataFrame(columns=FIELDS); graph=PatternGraph(empty); retriever=TextRetriever(empty)
    result=DesignAgent(empty,graph,retriever).run("想用植物花卉纹")
    assert not result["candidates"] and "放宽" in result["message"]


def test_rank_missing_field_not_match(sample_frame):
    graph=PatternGraph(sample_frame); result=DesignAgent(sample_frame,graph,TextRetriever(sample_frame)).run("宋代简洁")
    assert all("历史时期=宋" in x["unmatched"] for x in result["candidates"])
    assert all(any("时代" in risk for risk in x["risks"]) for x in result["candidates"])


def test_complete_structured_match_scores_one(sample_frame):
    frame=sample_frame.iloc[[0]].copy()
    frame.loc[frame.index[0],"historical_period"]="宋代"
    frame.loc[frame.index[0],"application_context"]="文房、茶具"
    frame.at[frame.index[0],"visual_keywords"]=["简洁","雅致"]
    result=DesignAgent(frame,PatternGraph(frame),TextRetriever(frame)).run("宋代文房茶具，简洁雅致，寓意清雅")
    candidate=result["candidates"][0]
    assert candidate["structured_score"]==1.0
    assert "历史时期=宋" in candidate["matched"] and not candidate["unmatched"]


def test_candidate_without_cultural_evidence_is_explicit(sample_frame):
    frame=sample_frame.iloc[[0]].copy()
    frame.loc[frame.index[0],["summary","cultural_meaning"]]=""
    retriever=TextRetriever(frame)
    result=DesignAgent(frame,PatternGraph(frame),retriever).run("简洁瓷器")
    assert retriever.documents==[]
    assert result["evidence"]==[] and result["candidates"][0]["evidence"] is None
    assert result["candidates"][0]["text_score"]==0
