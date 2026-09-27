"""Regression coverage for the public catalogue and AI dessert endpoints."""
from pathlib import Path

import requests


def base_url():
    env = Path(__file__).parents[2] / "frontend" / ".env"
    value = next(line.split("=", 1)[1].strip() for line in env.read_text().splitlines() if line.startswith("REACT_APP_BACKEND_URL="))
    return value.rstrip("/")


BASE = base_url()

REQUIRED_PRODUCT_FIELDS = {"id", "name", "price", "serves", "moods", "occasions", "image", "story"}


def test_root():
    root = requests.get(f"{BASE}/api/", timeout=20)
    assert root.status_code == 200
    assert root.json()["message"] == "Treats & Temptation by SK API"


def test_products_exactly_eight_with_fields():
    response = requests.get(f"{BASE}/api/products", timeout=20)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 8, f"Expected 8 products, got {len(data)}"
    for p in data:
        missing = REQUIRED_PRODUCT_FIELDS - set(p.keys())
        assert not missing, f"Product {p.get('id')} missing fields: {missing}"


def _match(payload):
    r = requests.post(f"{BASE}/api/match", json=payload, timeout=60)
    assert r.status_code == 200, r.text
    return r.json()


def test_match_explanation_contains_only_returned_product_name():
    # Fetch full catalogue for cross-check
    all_products = requests.get(f"{BASE}/api/products", timeout=20).json()
    all_names = [p["name"] for p in all_products]

    combos = [
        {"occasion": "Tea party", "mood": "Warm & comforting", "people": 6, "budget": 1000, "dietary": "No preference"},
        {"occasion": "Birthday", "mood": "Chocolate lover", "people": 8, "budget": 1500, "dietary": "No preference"},
        {"occasion": "Gift", "mood": "Fresh & citrusy", "people": 4, "budget": 900, "dietary": "Eggless"},
    ]
    for c in combos:
        data = _match(c)
        assert "product" in data and "explanation" in data
        picked = data["product"]["name"]
        explanation = data["explanation"]
        assert picked.lower() in explanation.lower(), f"Picked '{picked}' not in explanation: {explanation}"
        # No other catalogue name may appear
        others = [n for n in all_names if n != picked]
        for n in others:
            assert n.lower() not in explanation.lower(), (
                f"Explanation for {picked} contains other product '{n}': {explanation}"
            )


def test_chat_returns_reply_session_and_ok():
    r = requests.post(f"{BASE}/api/chat", json={"message": "What is good for a tea party for 6?"}, timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"].startswith("chat-") or data["session_id"].startswith("match-") or data["session_id"]
    assert isinstance(data["reply"], str) and data["reply"]
    assert data["ok"] is True
    # Validate at least one catalogue product name appears
    all_products = requests.get(f"{BASE}/api/products", timeout=20).json()
    names = [p["name"] for p in all_products]
    reply_lower = data["reply"].lower()
    assert any(n.lower() in reply_lower for n in names), f"Reply mentions no catalogue product: {data['reply']}"
