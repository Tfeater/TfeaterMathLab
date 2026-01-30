import json

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_parse_natural_language_fallback_on_failure(client, monkeypatch):
    """
    When the natural language parser cannot handle input, the view should
    return a unified fallback response instead of a raw error.
    """
    from solver import views

    class DummyParser:
        def parse(self, text):
            return None

    monkeypatch.setattr(views, "NaturalLanguageParser", lambda: DummyParser())

    url = reverse("parse_natural")
    payload = {"text": "This is not a math expression at all"}
    response = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "fallback"
    assert data["target_tab"] == "text"
    assert data["original_input"] == payload["text"]


@pytest.mark.django_db
def test_ai_explanations_only_after_engine_success(client, monkeypatch):
    """
    If the math engine fails, the endpoint should fall back to Text instead of
    attempting AI explanations.
    """
    # Force the engine to raise an error
    from solver import views

    def broken_simplify(expression):
        return {"error": "forced failure"}

    monkeypatch.setattr(views.math_engine, "simplify", broken_simplify)

    url = reverse("solve")
    payload = {
        "operation": "simplify",
        "expression": "x^2 - 4",
        "original_input": "x^2 - 4",
        "save_history": False,
    }
    response = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "fallback"
    assert data["target_tab"] == "text"


@pytest.mark.django_db
def test_fallback_response_schema_is_stable(client):
    """
    Ensure the fallback schema always contains the required keys.
    """
    url = reverse("solve")
    payload = {
        "operation": "solve",
        "expression": "x**+",  # invalid
        "original_input": "x**+",
        "save_history": False,
    }
    resp = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    data = resp.json()
    assert set(["status", "target_tab", "original_input", "error_type", "error_message"]) <= set(data.keys())
