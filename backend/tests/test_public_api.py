"""Regression coverage for the Treats & Temptation public API (7-loaf iteration)."""
from pathlib import Path

import pytest
import requests


def base_url():
    env = Path(__file__).parents[2] / "frontend" / ".env"
    value = next(line.split("=", 1)[1].strip() for line in env.read_text().splitlines() if line.startswith("REACT_APP_BACKEND_URL="))
    return value.rstrip("/")


BASE = base_url()

REQUIRED_PRODUCT_FIELDS = {"id", "name", "price", "serves", "moods", "occasions", "image", "story"}

EXPECTED_LOAF_IDS = {
    "chocolate-chip-banana",
    "apple-cinnamon",
    "lemon-loaf",
    "coconut-loaf",
    "coffee-walnut-loaf",
    "double-chocolate",
    "chocolate-malt",
}

EXPECTED_BOX_IDS = {"anniversary-box", "birthday-box", "graduation-box", "eid-box", "baby-born-box"}


# ---------- Root ----------
def test_root():
    r = requests.get(f"{BASE}/api/", timeout=20)
    assert r.status_code == 200
    assert r.json()["message"] == "Treats & Temptation by SK API"


# ---------- Products ----------
def test_products_exactly_seven_loaves_with_addons():
    r = requests.get(f"{BASE}/api/products", timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 7, f"Expected 7 loaves, got {len(data)}"
    ids = {p["id"] for p in data}
    assert ids == EXPECTED_LOAF_IDS, f"Unexpected ids: {ids}"
    for p in data:
        missing = REQUIRED_PRODUCT_FIELDS - set(p.keys())
        assert not missing, f"Product {p.get('id')} missing: {missing}"

    banana = next(p for p in data if p["id"] == "chocolate-chip-banana")
    assert "addons" in banana and isinstance(banana["addons"], list) and banana["addons"], \
        "Chocolate Chip Banana Bread must have non-empty addons"
    walnut = next((a for a in banana["addons"] if a["name"].lower() == "walnuts"), None)
    assert walnut is not None, "Walnuts add-on missing"
    assert walnut["price"] == 100


# ---------- Festive boxes ----------
def test_festive_boxes_five_and_totals_match():
    products = requests.get(f"{BASE}/api/products", timeout=20).json()
    pmap = {p["id"]: p for p in products}

    r = requests.get(f"{BASE}/api/festive-boxes", timeout=20)
    assert r.status_code == 200
    boxes = r.json()
    assert len(boxes) == 5
    ids = {b["id"] for b in boxes}
    assert ids == EXPECTED_BOX_IDS

    for b in boxes:
        assert isinstance(b.get("total"), (int, float))
        assert b["items"], f"Box {b['id']} has no items"
        computed = 0
        for it in b["items"]:
            assert "product" in it and "qty" in it, f"Box {b['id']} item not hydrated"
            assert it["product"]["id"] in pmap
            computed += it["product"]["price"] * it["qty"]
        assert computed == b["total"], f"Box {b['id']} total mismatch: {computed} vs {b['total']}"


# ---------- Matchmaker ----------
def _match(payload):
    r = requests.post(f"{BASE}/api/match", json=payload, timeout=60)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("payload", [
    {"occasion": "Eid", "mood": "Something different", "people": 6, "budget": 1500, "dietary": "No preference"},
    {"occasion": "Graduation", "mood": "Coffee lover", "people": 6, "budget": 2000, "dietary": "No preference"},
    {"occasion": "Baby born", "mood": "Fresh & citrusy", "people": 6, "budget": 1300, "dietary": "No preference"},
])
def test_match_explanation_contains_only_picked_name(payload):
    all_products = requests.get(f"{BASE}/api/products", timeout=20).json()
    all_names = [p["name"] for p in all_products]

    data = _match(payload)
    assert "product" in data and "explanation" in data
    picked = data["product"]["name"]
    exp = data["explanation"]
    assert picked.lower() in exp.lower(), f"Picked '{picked}' missing in explanation: {exp}"
    for n in all_names:
        if n != picked:
            assert n.lower() not in exp.lower(), f"Explanation for {picked} leaks '{n}': {exp}"


# ---------- Save/Load match ----------
def test_save_and_get_match_roundtrip():
    match = _match({"occasion": "Eid", "mood": "Something different", "people": 6, "budget": 1500, "dietary": "No preference"})
    payload = {
        "product_id": match["product"]["id"],
        "occasion": "Eid",
        "mood": "Something different",
        "people": 6,
        "budget": 1500,
        "dietary": "No preference",
        "explanation": match["explanation"],
    }
    r = requests.post(f"{BASE}/api/match/save", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "id" in body
    mid = body["id"]
    assert isinstance(mid, str) and len(mid) == 10
    int(mid, 16)  # must be hex

    got = requests.get(f"{BASE}/api/match/{mid}", timeout=20)
    assert got.status_code == 200
    data = got.json()
    assert data["id"] == mid
    assert data["product"]["id"] == match["product"]["id"]
    assert data["explanation"] == match["explanation"]


def test_get_match_not_found():
    r = requests.get(f"{BASE}/api/match/does-not-exist", timeout=20)
    assert r.status_code == 404


def test_save_match_unknown_product_404():
    r = requests.post(f"{BASE}/api/match/save", json={
        "product_id": "not-a-real-id",
        "occasion": "Eid", "mood": "Something different", "people": 6, "budget": 1500,
        "dietary": "No preference", "explanation": "test",
    }, timeout=20)
    assert r.status_code == 404


# ---------- Chat ----------
def test_chat_returns_reply_and_only_catalogue():
    r = requests.post(f"{BASE}/api/chat", json={"message": "What loaf for a tea party for 6?"}, timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert isinstance(data["reply"], str) and data["reply"]
    assert isinstance(data["session_id"], str) and data["session_id"]

    products = requests.get(f"{BASE}/api/products", timeout=20).json()
    names = [p["name"] for p in products]
    reply_lower = data["reply"].lower()
    # Reply may not always mention a name, but if it does, must be from catalogue.
    # We only enforce: no obviously invented loaf mentioned (heuristic: word 'loaf' present -> some catalogue name should appear)
    if "loaf" in reply_lower or "bread" in reply_lower:
        assert any(n.lower() in reply_lower for n in names), f"Reply mentions no catalogue product: {data['reply']}"
