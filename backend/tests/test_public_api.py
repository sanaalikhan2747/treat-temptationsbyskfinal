"""Regression coverage for Treats & Temptation public API — 19-item + orders iteration."""
from pathlib import Path
import re
import pytest
import requests


def base_url():
    env = Path(__file__).parents[2] / "frontend" / ".env"
    value = next(line.split("=", 1)[1].strip() for line in env.read_text().splitlines() if line.startswith("REACT_APP_BACKEND_URL="))
    return value.rstrip("/")


BASE = base_url()

CUSTOM_BOX_IDS = {
    "brownies-batch", "cinnamon-rolls-batch", "papparoti-batch", "cadbury-eclair-batch",
    "chocolate-chip-cookie", "chocolate-filled-cookie", "lotus-cookie", "double-chocolate-cookie",
}


def test_root():
    r = requests.get(f"{BASE}/api/", timeout=20)
    assert r.status_code == 200
    assert r.json()["message"] == "Treats & Temptation by SK API"


# ---------- Products ----------
def test_products_19_items_across_4_categories():
    r = requests.get(f"{BASE}/api/products", timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 19, f"Expected 19 items, got {len(data)}"
    cats = {}
    for p in data:
        assert {"id", "name", "category", "price", "image", "moods", "occasions"} <= set(p.keys()), \
            f"Missing fields on {p.get('id')}"
        cats.setdefault(p["category"], []).append(p["id"])
    assert len(cats.get("loaf", [])) == 6
    assert len(cats.get("cheesecake", [])) == 5
    assert len(cats.get("batch", [])) == 4
    assert len(cats.get("cookie", [])) == 4


def test_custom_box_unit_only_on_expected_items():
    products = requests.get(f"{BASE}/api/products", timeout=20).json()
    with_cbox = {p["id"] for p in products if "custom_box_unit" in p}
    assert with_cbox == CUSTOM_BOX_IDS, f"Mismatch: {with_cbox ^ CUSTOM_BOX_IDS}"
    # Spot-check specific prices
    prices = {p["id"]: p.get("custom_box_unit") for p in products if "custom_box_unit" in p}
    assert prices["brownies-batch"] == 275
    assert prices["cinnamon-rolls-batch"] == 375
    assert prices["papparoti-batch"] == 225
    assert prices["cadbury-eclair-batch"] == 250


def test_packaging_three_options():
    r = requests.get(f"{BASE}/api/packaging", timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    by = {p["id"]: p for p in data}
    assert set(by.keys()) == {"clear-box", "white-box", "kraft-box"}
    styles = {"clear-box": "clear", "white-box": "white", "kraft-box": "kraft"}
    for pid, style in styles.items():
        opt = by[pid]
        assert opt["price"] == 150
        assert opt["ribbon"] == "pink"
        assert opt["style"] == style
        assert "customer-assets-rejwkqb3.emergentagent" in opt["image"]


def test_festive_boxes_five_and_totals():
    products = requests.get(f"{BASE}/api/products", timeout=20).json()
    pmap = {p["id"]: p for p in products}
    r = requests.get(f"{BASE}/api/festive-boxes", timeout=20)
    assert r.status_code == 200
    boxes = r.json()
    assert len(boxes) == 5
    for b in boxes:
        computed = sum(pmap[it["product"]["id"]]["price"] * it["qty"] for it in b["items"])
        assert computed == b["total"], f"Box {b['id']} total mismatch"


# ---------- Match regression ----------
def test_match_returns_loaf_with_name_in_explanation():
    r = requests.post(f"{BASE}/api/match", json={
        "occasion": "Eid", "mood": "Something different", "people": 6, "budget": 1500, "dietary": "No preference",
    }, timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert data["product"]["category"] == "loaf"
    assert data["product"]["name"].lower() in data["explanation"].lower()


# ---------- Orders ----------
def _customer():
    return {"name": "TEST Buyer", "phone": "03001234567", "address": "House 1, Karachi", "delivery_date": "2026-02-14"}


def test_order_happy_path():
    payload = {
        "items": [
            {"product_id": "brownies-batch", "qty": 2, "custom_box": True},
            {"product_id": "chocolate-chip-cookie", "qty": 4, "custom_box": True},
        ],
        "packaging_id": "kraft-box",
        "personalized_message": "Happy birthday",
        "customer": _customer(),
    }
    r = requests.post(f"{BASE}/api/orders", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert re.match(r"^TT\d{6}$", body["order_number"])
    prices = {i["product_id"]: i["unit_price"] for i in body["items"]}
    assert prices["brownies-batch"] == 275
    assert prices["chocolate-chip-cookie"] == 200
    assert body["subtotal"] == 275 * 2 + 200 * 4  # 1350
    assert body["packaging"]["ribbon"] == "pink"
    assert body["packaging"]["style"] == "kraft"
    assert "customer-assets-rejwkqb3.emergentagent" in body["packaging"]["image"]
    assert body["packaging_total"] == 150
    assert body["total"] == 1500
    assert body["status"] == "pending_confirmation"

    # GET persistence
    g = requests.get(f"{BASE}/api/orders/{body['order_number']}", timeout=20)
    assert g.status_code == 200
    assert g.json()["order_number"] == body["order_number"]
    assert g.json()["total"] == 1500


def test_order_custom_box_on_non_cbox_product_400():
    r = requests.post(f"{BASE}/api/orders", json={
        "items": [{"product_id": "lemon-loaf", "qty": 1, "custom_box": True}],
        "customer": _customer(),
    }, timeout=20)
    assert r.status_code == 400


def test_order_unknown_product_404():
    r = requests.post(f"{BASE}/api/orders", json={
        "items": [{"product_id": "fake", "qty": 1}], "customer": _customer(),
    }, timeout=20)
    assert r.status_code == 404


def test_order_empty_items_400():
    r = requests.post(f"{BASE}/api/orders", json={"items": [], "customer": _customer()}, timeout=20)
    assert r.status_code == 400


def test_order_unknown_number_404():
    r = requests.get(f"{BASE}/api/orders/UNKNOWN", timeout=20)
    assert r.status_code == 404


# ---------- Iteration 5: festive box by id + new imagery ----------
NEW_PHOTO_IDS = ["1617118601021", "1700045530510", "1764385827123", "1513201099705"]


def test_festive_boxes_new_image_urls():
    r = requests.get(f"{BASE}/api/festive-boxes", timeout=20)
    assert r.status_code == 200
    boxes = r.json()
    assert len(boxes) == 5
    for b in boxes:
        assert any(pid in b["image"] for pid in NEW_PHOTO_IDS), \
            f"Box {b['id']} image not from new photo set: {b['image']}"


def test_get_festive_box_eid_hydrated():
    r = requests.get(f"{BASE}/api/festive-boxes/eid-box", timeout=20)
    assert r.status_code == 200
    b = r.json()
    assert b["id"] == "eid-box"
    ids_qty = {it["product"]["id"]: it["qty"] for it in b["items"]}
    assert ids_qty == {"coconut-loaf": 1, "lotus-cookie": 4, "papparoti-batch": 1}
    # Total = 1200 + 4*300 + 800 = 3200
    assert b["total"] == 3200


def test_get_festive_box_unknown_404():
    r = requests.get(f"{BASE}/api/festive-boxes/unknown-box", timeout=20)
    assert r.status_code == 404


def test_order_from_festive_editor_uses_full_prices():
    # Simulates order placed from FestiveBoxEditor: custom_box=False, full prices.
    payload = {
        "items": [
            {"product_id": "coconut-loaf", "qty": 1, "custom_box": False},
            {"product_id": "lotus-cookie", "qty": 4, "custom_box": False},
            {"product_id": "papparoti-batch", "qty": 1, "custom_box": False},
        ],
        "packaging_id": "clear-box",
        "customer": _customer(),
    }
    r = requests.post(f"{BASE}/api/orders", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    prices = {i["product_id"]: i["unit_price"] for i in body["items"]}
    assert prices["coconut-loaf"] == 1200
    assert prices["lotus-cookie"] == 300
    assert prices["papparoti-batch"] == 800
    assert body["subtotal"] == 1200 + 4 * 300 + 800  # 3200
    assert body["total"] == 3200 + 150
    assert body["packaging"]["style"] == "clear"


# ---------- Iteration 6: new packaging ----------
def test_order_old_packaging_id_404():
    r = requests.post(f"{BASE}/api/orders", json={
        "items": [{"product_id": "coconut-loaf", "qty": 1}],
        "packaging_id": "pink-ribbon",
        "customer": _customer(),
    }, timeout=20)
    assert r.status_code == 404


def test_order_coconut_loaf_kraft_box_total():
    r = requests.post(f"{BASE}/api/orders", json={
        "items": [{"product_id": "coconut-loaf", "qty": 1}],
        "packaging_id": "kraft-box",
        "customer": _customer(),
    }, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["subtotal"] == 1200
    assert body["packaging_total"] == 150
    assert body["total"] == 1350
    assert body["packaging"]["style"] == "kraft"
    assert body["packaging"]["name"] == "Brown Kraft Box with Pink Ribbon"


def test_chat_endpoint():
    r = requests.post(f"{BASE}/api/chat", json={"message": "What do you recommend for tea?"}, timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data and "session_id" in data


def test_match_save_and_get():
    m = requests.post(f"{BASE}/api/match", json={
        "occasion": "Tea party", "mood": "Warm & comforting", "people": 6, "budget": 1500,
    }, timeout=60).json()
    save = requests.post(f"{BASE}/api/match/save", json={
        "product_id": m["product"]["id"], "occasion": "Tea party", "mood": "Warm & comforting",
        "people": 6, "budget": 1500, "explanation": m["explanation"],
    }, timeout=20)
    assert save.status_code == 200
    mid = save.json()["id"]
    g = requests.get(f"{BASE}/api/match/{mid}", timeout=20)
    assert g.status_code == 200
    assert g.json()["product"]["id"] == m["product"]["id"]
