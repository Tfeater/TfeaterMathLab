import base64
import json

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from solver.models import Calculation


@pytest.mark.django_db
def test_graph_generation_success(client):
    url = reverse("generate_graph")
    payload = {
        "expression": "x^2",
        "x_min": -5,
        "x_max": 5,
    }
    response = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    assert "status" not in data or data.get("status") != "fallback"
    assert "image" in data and data["image"]
    # Basic check that this is base64-ish
    base64.b64decode(data["image"], validate=True)


@pytest.mark.django_db
def test_graph_generation_fallback_on_invalid_expression(client):
    url = reverse("generate_graph")
    payload = {
        "expression": "x**+",
        "x_min": -5,
        "x_max": 5,
    }
    response = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "fallback"
    assert data["target_tab"] == "text"


@pytest.mark.django_db
def test_pdf_export_current_uses_latest_calculation(client):
    # Create a user and a sample calculation
    user = User.objects.create_user(username="tester", password="password123")
    calc = Calculation.objects.create(
        user=user,
        operation_type="solve",
        original_input="2*x + 5 = 15",
        parsed_math_expression="2*x + 5 = 15",
        result="5",
        latex_result="5",
        steps=["Step 1: 2*x + 5 = 15", "Step 2: x = 5"],
    )

    client.force_login(user)
    url = reverse("export_pdf_current")
    response = client.get(url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert int(response["Content-Length"]) > 0
