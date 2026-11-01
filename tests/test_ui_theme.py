from pathlib import Path


def test_streamlit_theme_has_dark_text_on_light_background():
    config = Path(".streamlit/config.toml").read_text(encoding="utf-8")
    assert 'base = "light"' in config
    assert 'backgroundColor = "#F4F1E9"' in config
    assert 'textColor = "#292923"' in config


def test_css_overrides_widget_and_placeholder_contrast():
    app = Path("app.py").read_text(encoding="utf-8")
    assert 'input::placeholder' in app
    assert '[data-testid="stSidebar"] h1' in app
    assert '[data-testid="stFileUploader"] section' in app
    assert 'color:var(--ink)!important' in app
