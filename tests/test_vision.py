import io

import numpy as np
import pytest

from src.vision import analyze_features, extract_features, feature_frame, visual_neighbors


def test_extract_visual_feature(image_paths):
    feat=extract_features(image_paths[0])
    assert feat["vector"].shape==(33,) and feat["dominant_hex"].startswith("#")
    assert len(feat["palette_hex"])==5


def test_similar_image_retrieval(sample_frame,image_paths):
    index,vectors=feature_frame(sample_frame)
    hits=visual_neighbors(image_paths[0],index,vectors,2)
    assert hits[0]["name"]=="莲纹" and hits[0]["distance"]==pytest.approx(0)


def test_pca_cluster_has_real_metrics(sample_frame):
    index,vectors=feature_frame(sample_frame); result=analyze_features(index,vectors,2)
    assert {"pc1","pc2","cluster","silhouette"}.issubset(result.columns)
    assert np.isfinite(result.silhouette.iloc[0])


def test_corrupt_image_is_reported():
    with pytest.raises(ValueError,match="无法读取图片"): extract_features(io.BytesIO(b"not image"))
