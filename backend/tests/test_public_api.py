"""Regression coverage for the public catalogue and AI dessert endpoints."""
import os
from pathlib import Path

import requests


def base_url():
    env = Path(__file__).parents[2] / "frontend" / ".env"
    value = next(line.split("=", 1)[1].strip() for line in env.read_text().splitlines() if line.startswith("REACT_APP_BACKEND_URL="))
    return value.rstrip("/")


def test_root_and_products():
    root = requests.get(f"{base_url()}/api/", timeout=20)
    products = requests.get(f"{base_url()}/api/products", timeout=20)
    assert root.status_code == 200
    assert root.json()["message"] == "Treats & Temptation by SK API"
    assert products.status_code == 200
    assert len(products.json()) == 4


def test_match_returns_catalogue_product():
    response = requests.post(
        f"{base_url()}/api/match",
        json={"occasion": "Tea party", "mood": "Warm & comforting", "people": 6, "budget": 1000, "dietary": "No preference"},
        timeout=60,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["product"]["id"] in {"chocolate-cake", "cinnamon-rolls", "banana-loaf", "brownies"}
    assert data["explanation"]


def test_chat_returns_reply_and_session():
    response = requests.post(f"{base_url()}/api/chat", json={"message": "What is good for a gift?"}, timeout=60)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"].startswith("chat-")
    assert data["reply"]