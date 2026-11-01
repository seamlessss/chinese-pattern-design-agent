from __future__ import annotations

import pandas as pd
import pytest
from PIL import Image

from src.data.loader import FIELDS


@pytest.fixture
def image_paths(tmp_path):
    paths=[]
    for name,color in [("red.png",(220,30,20)),("blue.png",(20,30,220)),("red2.png",(200,35,25))]:
        path=tmp_path/name; Image.new("RGB",(32,32),color).save(path); paths.append(path)
    return paths


@pytest.fixture
def sample_frame(image_paths):
    rows=[]
    for i,(name,category,meaning,keywords) in enumerate([("莲纹","植物纹","清雅、生生不息",["简洁","莲花"]),("龙纹","动物纹","吉祥",["华丽","龙"]),("回纹","几何纹","绵延",["简洁","连续"]) ]):
        row={c:"" for c in FIELDS}; row.update({"pattern_id":f"test:{i}","name":name,"name_en":"","category":category,"historical_period":"","cultural_meaning":meaning,"application_context":"瓷器" if i==0 else "","visual_keywords":keywords,"summary":meaning+" "+" ".join(keywords),"image_path":str(image_paths[i]),"source_name":"测试 fixture","source_url":"local:test","license":"test-only","source_record_id":str(i),"source_file_path":"fixture","related_patterns":[],"evidence_status":"测试 fixture","evidence_type":"dataset_description","external_evidence_status":"not_available"}); rows.append(row)
    return pd.DataFrame(rows,columns=FIELDS)
