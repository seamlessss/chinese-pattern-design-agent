import base64
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest
import requests as requests_lib

from src.generation import (
    BailianImageProvider,
    GenerationError,
    GenerationResult,
    OpenAIImageProvider,
    bailian_api_key,
    build_pattern_prompt,
    generate_programmatic_svg,
    image_api_key,
    save_generation,
    validate_design_input,
)


class FakeResponse:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self.body = body or {}

    def json(self):
        return self.body


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.error:
            raise self.error
        return self.response


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j2ioAAAAASUVORK5CYII="
)


class BailianResponse(FakeResponse):
    def __init__(self, status=200, body=None, content=b""):
        super().__init__(status, body)
        self.content = content


class BailianSession:
    def __init__(self, polls, image=PNG_BYTES):
        self.polls = list(polls)
        self.image = image
        self.posts = []
        self.gets = []

    def post(self, *args, **kwargs):
        self.posts.append((args, kwargs))
        return BailianResponse(body={"output": {"task_id": "task-123"}})

    def get(self, url, **kwargs):
        self.gets.append((url, kwargs))
        if url == "https://example.org/result.png":
            return BailianResponse(content=self.image)
        return BailianResponse(body={"output": self.polls.pop(0)})


def test_prompt_contains_design_constraints_and_traced_reference():
    reference = {
        "pattern_id": "wenyang:001", "name": "缠枝莲纹", "visual_keywords": ["莲花", "连续藤蔓"],
        "summary": "数据集对纹样的描述", "source_name": "Wényàng", "source_url": "https://example.org/source",
        "license": "CC BY-NC 4.0", "historical_period": "",
    }
    prompt, metadata = build_pattern_prompt("莲花与藤蔓", "新中式", ["#FAF8F2", "#9E4037"], "茶具", "留白", reference)
    assert "莲花与藤蔓" in prompt and "新中式" in prompt and "茶具" in prompt
    assert "not provided and not verified" in prompt
    assert "historical" in prompt.lower() and "not independently verified" in prompt.lower()
    assert metadata["reference"]["pattern_id"] == "wenyang:001"
    assert "https://example.org/source" in prompt


def test_prompt_marks_reference_text_as_unverified_dataset_description():
    prompt, _ = build_pattern_prompt("回纹", "现代简约", ["#292923"], "包装", reference={"name":"回纹", "summary":"绵延寓意", "visual_keywords":["连续"], "pattern_id":"wenyang:041"})
    assert "unverified dataset description" in prompt
    assert "do not infer a dynasty" in prompt


@pytest.mark.parametrize("kwargs", [
    {"theme":"x", "style":"现代简约", "palette":["#FFFFFF"], "scene":"茶具"},
    {"theme":"山水纹", "style":"不存在风格", "palette":["#FFFFFF"], "scene":"茶具"},
    {"theme":"山水纹", "style":"现代简约", "palette":["red"], "scene":"茶具"},
    {"theme":"山水纹", "style":"现代简约", "palette":[], "scene":"茶具"},
    {"theme":"山水纹", "style":"现代简约", "palette":["#FFFFFF"], "scene":"不存在场景"},
    {"theme":"山水纹", "style":"现代简约", "palette":["#FFFFFF"], "scene":"茶具", "requirements":"x"*501},
])
def test_input_validation_rejects_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        validate_design_input(**kwargs)


def test_valid_input_normalizes_color_and_whitespace():
    result = validate_design_input("  云纹  ", "现代简约", ["#abcdef"], "包装", " 克制 ")
    assert result["theme"] == "云纹" and result["palette"] == ["#ABCDEF"]


def test_api_key_resolves_env_before_secrets_without_exposing_value():
    assert image_api_key({"OPENAI_API_KEY":" env-key "}, {"OPENAI_API_KEY":"secret-key"}) == "env-key"
    assert image_api_key({}, {"OPENAI_API_KEY":" secret-key "}) == "secret-key"
    assert image_api_key({}, {}) == ""


def test_bailian_key_resolves_env_before_secrets():
    assert bailian_api_key({"DASHSCOPE_API_KEY":" env-key "}, {"DASHSCOPE_API_KEY":"secret"}) == "env-key"
    assert bailian_api_key({}, {"DASHSCOPE_API_KEY":" secret "}) == "secret"
    assert bailian_api_key({}, {}) == ""


def test_bailian_provider_submits_polls_and_downloads_png():
    session = BailianSession([
        {"task_status": "RUNNING"},
        {"task_status": "SUCCEEDED", "results": [{"url": "https://example.org/result.png"}]},
    ])
    provider = BailianImageProvider("test-key", session=session, sleeper=lambda _: None, poll_interval=0)
    result = provider.generate("an original Chinese decorative motif")
    _, request = session.posts[0]
    assert request["headers"]["X-DashScope-Async"] == "enable"
    assert request["json"]["model"] == "wanx-v1"
    assert request["json"]["parameters"]["size"] == "1024*1024"
    assert result.image_bytes == PNG_BYTES
    assert result.provider == "阿里云百炼 · 通义万相"


def test_bailian_missing_key_and_failed_task_are_friendly():
    with pytest.raises(GenerationError, match="DASHSCOPE_API_KEY"):
        BailianImageProvider("").generate("motif")
    session = BailianSession([{"task_status": "FAILED", "message": "quota exhausted"}])
    with pytest.raises(GenerationError, match="quota exhausted"):
        BailianImageProvider("secret", session=session, sleeper=lambda _: None).generate("motif")


def test_missing_api_key_has_clear_error():
    with pytest.raises(GenerationError, match="尚未配置 OPENAI_API_KEY"):
        OpenAIImageProvider("").generate("pattern prompt")


def test_openai_provider_posts_prompt_and_returns_png():
    session = FakeSession(FakeResponse(body={"data":[{"b64_json":base64.b64encode(PNG_BYTES).decode()}]}))
    provider = OpenAIImageProvider("test-key", timeout=999, quality="medium", session=session)
    result = provider.generate("an original motif")
    args, request = session.calls[0]
    assert args[0] == provider.endpoint
    assert request["json"]["prompt"] == "an original motif"
    assert request["json"]["quality"] == "medium"
    assert request["timeout"] == 180
    assert result.image_bytes == PNG_BYTES and result.mime_type == "image/png"


def test_api_failure_is_sanitized():
    session = FakeSession(FakeResponse(status=429))
    with pytest.raises(GenerationError, match="HTTP 429"):
        OpenAIImageProvider("never-echo-this", session=session).generate("motif")


def test_api_timeout_has_friendly_error():
    session = FakeSession(error=requests_lib.Timeout())
    with pytest.raises(GenerationError, match="请求超时"):
        OpenAIImageProvider("test-key", session=session).generate("motif")


def test_programmatic_fallback_returns_original_svg():
    result = generate_programmatic_svg("云纹", "传统装饰", ["#F4F1E9", "#9E4037"], "茶具")
    assert result.startswith(b"<svg") and b"<pattern" in result
    assert "程序化生成纹样" in result.decode("utf-8")
    assert b"#9E4037" in result
    ElementTree.fromstring(result)


def test_saved_artifact_keeps_type_parameters_and_reference(tmp_path):
    result = GenerationResult(b"<svg xmlns='http://www.w3.org/2000/svg'></svg>", "image/svg+xml", "Programmatic SVG", "pattern-tile-v1", "720x360")
    artifact = save_generation(result, "a prompt", {"theme":"云纹", "reference":{"pattern_id":"wenyang:061"}}, tmp_path)
    metadata = json.loads(Path(artifact["metadata_path"]).read_text(encoding="utf-8"))
    assert artifact["label"] == "程序化生成"
    assert metadata["reference_pattern_id"] == "wenyang:061"
    assert Path(artifact["image_path"]).read_bytes() == result.image_bytes
    bailian_api_key,
