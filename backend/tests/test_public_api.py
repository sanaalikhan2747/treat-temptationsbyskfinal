"""Regression coverage for Treats & Temptation public API — 28-item full menu + variants & packs."""
from pathlib import Path
import re
import pytest
from starlette.testclient import TestClient
import sys

# Ensure backend directory is in python path
sys.path.insert(0, str(Path(__file__).parents[1]))
from server import app, PRODUCTS

client = TestClient(app)

CUSTOM_BOX_IDS = {
    "brownies-batch",
    "cinnamon-rolls-batch",
    "papparoti-batch",
    "flourless-brownies",
    "chocolate-chip-cookie",
    "double-chocolate-cookie",
    "oat-flour-cookie",
    "mango-trifle",
    "chocolate-trifle",
    "malt-cake",
}


def test_root():
    r = client.get("/api/")
    assert r.status_code == 200
    assert r.json()["message"] == "Treats & Temptation by SK API"


# ---------- Products ----------
def test_products_28_items_across_categories():
    r = client.get("/api/products")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 28, f"Expected 28 items, got {len(data)}"
    cats = {}
    for p in data:
        assert {"id", "name", "category", "price", "image", "moods", "occasions"} <= set(p.keys()), \
            f"Missing fields on {p.get('id')}"
        cats.setdefault(p["category"], []).append(p["id"])
    assert len(cats.get("loaf", [])) == 9
    assert len(cats.get("cheesecake", [])) == 7
    assert len(cats.get("batch", [])) == 8
    assert len(cats.get("cookie", [])) == 4

    # Verify Healthy Range items
    healthy_items = [p for p in data if p.get("healthy")]
    assert len(healthy_items) == 4
    healthy_ids = {p["id"] for p in healthy_items}
    assert healthy_ids == {
        "sugar-free-dates",
        "oat-flour-banana-bread",
        "flourless-brownies",
        "oat-flour-cookie",
    }


def test_custom_box_unit_only_on_expected_items():
    products = client.get("/api/products").json()
    with_cbox = {p["id"] for p in products if "custom_box_unit" in p}
    assert with_cbox == CUSTOM_BOX_IDS, f"Mismatch: {with_cbox ^ CUSTOM_BOX_IDS}"
    # Spot-check specific prices matching 2-page menu
    prices = {p["id"]: p.get("custom_box_unit") for p in products if "custom_box_unit" in p}
    assert prices["brownies-batch"] == 300
    assert prices["cinnamon-rolls-batch"] == 400
    assert prices["papparoti-batch"] == 300
    assert prices["chocolate-chip-cookie"] == 300
    assert prices["double-chocolate-cookie"] == 350
    assert prices["oat-flour-cookie"] == 400
    assert prices["mango-trifle"] == 350
    assert prices["chocolate-trifle"] == 400
    assert prices["malt-cake"] == 400


def test_packaging_three_options():
    r = client.get("/api/packaging")
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
    products = client.get("/api/products").json()
    pmap = {p["id"]: p for p in products}
    r = client.get("/api/festive-boxes")
    assert r.status_code == 200
    boxes = r.json()
    assert len(boxes) == 5
    for b in boxes:
        computed = sum(pmap[it["product"]["id"]]["price"] * it["qty"] for it in b["items"])
        assert computed == b["total"], f"Box {b['id']} total mismatch"


# ---------- Match regression ----------
def test_match_returns_loaf_with_name_in_explanation():
    r = client.post("/api/match", json={
        "occasion": "Eid", "mood": "Something different", "people": 6, "budget": 1500, "dietary": "No preference",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["product"]["category"] == "loaf"
    assert data["product"]["name"].lower() in data["explanation"].lower()


# ---------- Orders ----------
def _customer():
    return {"name": "TEST Buyer", "phone": "03001234567", "address": "House 1, Karachi", "delivery_date": "2026-10-15"}


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
    r = client.post("/api/orders", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert re.match(r"^TT\d{6}$", body["order_number"])
    prices = {i["product_id"]: i["unit_price"] for i in body["items"]}
    assert prices["brownies-batch"] == 300
    assert prices["chocolate-chip-cookie"] == 300
    assert body["subtotal"] == 300 * 2 + 300 * 4  # 1800
    assert body["packaging"]["ribbon"] == "pink"
    assert body["packaging"]["style"] == "kraft"
    assert "customer-assets-rejwkqb3.emergentagent" in body["packaging"]["image"]
    assert body["packaging_total"] == 150
    assert body["total"] == 1950
    assert body["status"] == "pending_confirmation"

    # GET persistence
    g = client.get(f"/api/orders/{body['order_number']}")
    assert g.status_code == 200
    assert g.json()["order_number"] == body["order_number"]
    assert g.json()["total"] == 1950


def test_order_with_variants_and_packs():
    # 1. New York Cheesecake with Strawberry Topping
    payload_variant = {
        "items": [
            {"product_id": "nyc-cheesecake", "qty": 1, "selected_variant": "Strawberry Topping"},
        ],
        "customer": _customer(),
    }
    r1 = client.post("/api/orders", json=payload_variant)
    assert r1.status_code == 200
    item1 = r1.json()["items"][0]
    assert item1["selected_variant"] == "Strawberry Topping"

    # 2. Cinnamon rolls pack of 4 with mix selection (2 Chocolate, 2 Vanilla)
    payload_pack = {
        "items": [
            {
                "product_id": "cinnamon-rolls-batch",
                "qty": 1,
                "pack_selection": {"Chocolate": 2, "Vanilla": 2},
            },
        ],
        "customer": _customer(),
    }
    r2 = client.post("/api/orders", json=payload_pack)
    assert r2.status_code == 200
    item2 = r2.json()["items"][0]
    assert item2["pack_selection"] == {"Chocolate": 2, "Vanilla": 2}

    # 3. Mini Loaves 4-pack mix (1 of each 4 flavors)
    payload_mini_loaves = {
        "items": [
            {
                "product_id": "mini-loaves-batch",
                "qty": 1,
                "pack_selection": {
                    "Lemon": 1,
                    "Coconut": 1,
                    "Coffee Walnut": 1,
                    "Double Chocolate": 1,
                },
            },
        ],
        "customer": _customer(),
    }
    r3 = client.post("/api/orders", json=payload_mini_loaves)
    assert r3.status_code == 200
    assert r3.json()["items"][0]["unit_price"] == 2000


def test_order_invalid_variant_400():
    r = client.post("/api/orders", json={
        "items": [{"product_id": "nyc-cheesecake", "qty": 1, "selected_variant": "Mango Topping"}],
        "customer": _customer(),
    })
    assert r.status_code == 400


def test_order_invalid_pack_count_400():
    r = client.post("/api/orders", json={
        "items": [
            {
                "product_id": "cinnamon-rolls-batch",
                "qty": 1,
                "pack_selection": {"Chocolate": 2, "Vanilla": 1},  # sum = 3, requires 4
            }
        ],
        "customer": _customer(),
    })
    assert r.status_code == 400


def test_order_invalid_pack_flavor_400():
    r = client.post("/api/orders", json={
        "items": [
            {
                "product_id": "cinnamon-rolls-batch",
                "qty": 1,
                "pack_selection": {"Chocolate": 2, "Blueberry": 2},  # Blueberry invalid
            }
        ],
        "customer": _customer(),
    })
    assert r.status_code == 400


def test_order_custom_box_on_non_cbox_product_400():
    r = client.post("/api/orders", json={
        "items": [{"product_id": "lemon-loaf", "qty": 1, "custom_box": True}],
        "customer": _customer(),
    })
    assert r.status_code == 400


def test_order_unknown_product_404():
    r = client.post("/api/orders", json={
        "items": [{"product_id": "fake", "qty": 1}], "customer": _customer(),
    })
    assert r.status_code == 404


def test_order_empty_items_400():
    r = client.post("/api/orders", json={"items": [], "customer": _customer()})
    assert r.status_code == 400


def test_order_unknown_number_404():
    r = client.get("/api/orders/UNKNOWN")
    assert r.status_code == 404


def test_order_coconut_loaf_kraft_box_total():
    r = client.post("/api/orders", json={
        "items": [{"product_id": "coconut-loaf", "qty": 1}],
        "packaging_id": "kraft-box",
        "customer": _customer(),
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["subtotal"] == 1200
    assert body["packaging_total"] == 150
    assert body["total"] == 1350
    assert body["packaging"]["style"] == "kraft"
    assert body["packaging"]["name"] == "Brown Kraft Box with Pink Ribbon"
