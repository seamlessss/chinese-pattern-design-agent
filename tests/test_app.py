from streamlit.testing.v1 import AppTest


def test_app_starts_and_has_navigation():
    app=AppTest.from_file("app.py",default_timeout=20).run()
    assert not app.exception
    assert any("纹样知策" in x.value for x in app.title)
    assert len(app.radio)>=1

