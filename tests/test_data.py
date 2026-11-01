import json

import pandas as pd

from src.data.huggingface_import import import_stage, validate_mapping
from src.data.loader import FIELDS, audit_patterns, normalize_wenyang


def test_wenyang_normalization_keeps_unknown(tmp_path):
    raw=[{"id":"001","name_cn":"莲纹","category":"植物","summary":"常见于瓷器。","meaning":"清雅","visual_keywords":["莲"]}]
    df=normalize_wenyang(raw,tmp_path)
    assert list(df.columns)==FIELDS and df.iloc[0].historical_period==""
    assert df.iloc[0].application_context=="瓷器"


def test_detail_page_explicit_context_and_related_mapping(tmp_path):
    detail=tmp_path/"patterns/a.md"; detail.parent.mkdir(parents=True)
    detail.write_text("## 常见载体\n茶具、文房。\n\n## 关联纹样\n回纹、并不存在纹。",encoding="utf-8")
    raw=[{"id":"001","name_cn":"莲纹","detail_page":"patterns/a.md"},{"id":"002","name_cn":"回纹"}]
    df=normalize_wenyang(raw,tmp_path)
    assert df.iloc[0].application_context=="茶具、文房"
    assert df.iloc[0].related_patterns==["wenyang:002"]


def test_missing_image_and_duplicate_audit(sample_frame):
    df=pd.concat([sample_frame,sample_frame.iloc[[0]]],ignore_index=True)
    df.loc[0,"image_path"]=""
    audit=audit_patterns(df)
    assert audit["duplicate_ids"]==1 and audit["missing_images"]==1


def test_empty_audit():
    audit=audit_patterns(pd.DataFrame(columns=FIELDS))
    assert audit["records"]==0 and audit["available_images"]==0


def test_empty_list_field_is_not_counted_as_covered(sample_frame):
    audit=audit_patterns(sample_frame)
    assert audit["field_coverage"]["related_patterns"]==0


def test_hf_requires_official_mapping(tmp_path):
    try: validate_mapping(tmp_path)
    except FileNotFoundError as exc: assert "官方映射" in str(exc)
    else: raise AssertionError("应拒绝猜测映射")


def test_hf_one_to_many_mapping_preserves_images(tmp_path):
    stage=tmp_path/"step_2"; (stage/"dataset_json"/"类").mkdir(parents=True); (stage/"dataset_image"/"类").mkdir(parents=True)
    (stage/"image_json_mapping.csv").write_text("image,json,match_type\n类/001.jpg,类/001.json,exact\n类/001_1.jpg,类/001.json,inherited\n",encoding="utf-8")
    annotation={"x":{"regions":[{"region_attributes":{"编号":"001"}}]}}
    (stage/"dataset_json"/"类"/"001.json").write_text(json.dumps(annotation,ensure_ascii=False),encoding="utf-8")
    df=import_stage(stage,"step_2")
    assert len(df)==2 and df.pattern_id.nunique()==2
