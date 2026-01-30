import json

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_solve_endpoint_success(client):
    url = reverse("solve")
    payload = {
        "operation": "solve",
        "expression": "2*x + 5 = 15",
        "original_input": "2*x + 5 = 15",
        "save_history": False,
    }
    response = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    assert "status" not in data or data.get("status") != "fallback"
    assert data["latex"] == "5"
    assert isinstance(data["steps"], list)
    # Each step must be a dict with title/latex/explanation (from StepSerializer)
    for step in data["steps"]:
        assert isinstance(step, dict)
        assert {"title", "latex", "explanation"} <= set(step.keys())


@pytest.mark.django_db
def test_solve_endpoint_fallback_on_invalid_expression(client):
    url = reverse("solve")
    payload = {
        "operation": "solve",
        "expression": "x**+",
        "original_input": "x**+",
        "save_history": False,
    }
    response = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    # Unified fallback schema
    assert data["status"] == "fallback"
    assert data["target_tab"] == "text"
    assert data["original_input"] == "x**+"
    assert "error_type" in data
    assert "error_message" in data


@pytest.mark.django_db
def test_limit_endpoint_success(client):
    url = reverse("solve")
    payload = {
        "operation": "limit",
        "expression": "sin(x)/x",
        "variable": "x",
        "point": "0",
        "side": "both",
        "save_history": False,
    }
    response = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    assert "status" not in data or data.get("status") != "fallback"
    assert data["latex"] in ("1", "1.0")


@pytest.mark.django_db
def test_derivative_endpoint_success(client):
    url = reverse("solve")
    payload = {
        "operation": "derivative",
        "expression": "x^3",
        "variable": "x",
        "order": 1,
        "save_history": False,
    }
    resp = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" not in data or data.get("status") != "fallback"
    assert "latex" in data and data["latex"]


@pytest.mark.django_db
def test_integral_endpoint_fallback_on_invalid_bounds(client):
    url = reverse("solve")
    payload = {
        "operation": "integral",
        "expression": "x^2",
        "variable": "x",
        "definite": True,
        "lower": 5,
        "upper": 1,  # invalid (lower >= upper)
        "save_history": False,
    }
    resp = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "fallback"
    assert data["target_tab"] == "text"


@pytest.mark.django_db
def test_matrix_endpoint_success(client):
    url = reverse("solve")
    payload = {
        "operation": "matrix",
        "matrix_operation": "determinant",
        "expression": "[[1,2],[3,4]]",
        "save_history": False,
    }
    resp = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" not in data or data.get("status") != "fallback"
    assert data["latex"]


@pytest.mark.django_db
def test_matrix_endpoint_fallback_on_invalid_matrix(client):
    url = reverse("solve")
    payload = {
        "operation": "matrix",
        "matrix_operation": "determinant",
        "expression": "not_a_matrix",
        "save_history": False,
    }
    resp = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "fallback"
    assert data["target_tab"] == "text"

