import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.parametrize("page,title",[
    ("纹样图鉴与详情","纹样图鉴"),("知识图谱","知识图谱浏览"),("视觉分析","视觉分析与纹样星图"),
    ("设计辅助智能体","设计辅助智能体"),("数据与方法","数据与方法说明"),
])
def test_each_page_renders(page,title):
    app=AppTest.from_file("app.py",default_timeout=40).run()
    app.radio[0].set_value(page)
    app.run()
    assert not app.exception
    assert any(title in x.value for x in app.title)


def test_agent_button_executes():
    app=AppTest.from_file("app.py",default_timeout=40).run()
    app.radio[0].set_value("设计辅助智能体")
    app.run()
    app.button[0].click()
    app.run()
    assert not app.exception
    assert any("工具调用记录" in x.value for x in app.subheader)


def test_creation_studio_renders_with_local_key_configuration(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("PATTERN_GENERATION_DIR", str(tmp_path))
    app=AppTest.from_file("app.py",default_timeout=40).run()
    app.radio[0].set_value("AI 纹样创作室")
    app.run()
    assert not app.exception
    assert any("AI 纹样创作室" in title.value for title in app.title)
    # A developer may have a local, git-ignored Streamlit secret. Both states
    # are valid; the dedicated provider unit tests cover the missing-key path.
    missing = any("未配置图像 API 密钥" in item.value for item in app.info)
    configured = any("已配置" in item.value for item in app.success)
    assert missing or configured
    assert app.button[0].disabled is missing


def test_programmatic_creation_renders_and_exposes_download(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("PATTERN_GENERATION_DIR", str(tmp_path))
    app=AppTest.from_file("app.py",default_timeout=40).run()
    app.radio[0].set_value("AI 纹样创作室")
    app.run()
    svg_button=next(button for button in app.button if "程序化 SVG" in button.label)
    svg_button.click()
    app.run()
    assert not app.exception
    assert any("创作结果" in item.value for item in app.subheader)
    assert len(app.get("download_button")) >= 2


def test_agent_candidate_opens_studio_with_reference(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PATTERN_GENERATION_DIR", str(tmp_path))
    app=AppTest.from_file("app.py",default_timeout=40).run()
    app.radio[0].set_value("设计辅助智能体")
    app.run()
    app.button[0].click()
    app.run()
    next(button for button in app.button if "以此纹样作为创作参考" in button.label).click()
    app.run()
    assert not app.exception
    assert app.radio[0].value=="AI 纹样创作室"
    assert any("检索参考" in item.value for item in app.markdown)
