from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
import uuid
import json
from datetime import datetime, timezone

try:
    from emergentintegrations.llm.chat import (
        LlmChat,
        UserMessage,
        TextDelta,
        StreamDone,
    )
except ImportError:
    LlmChat = UserMessage = TextDelta = StreamDone = None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get("DB_NAME", "treats_temptations")]

app = FastAPI()
api_router = APIRouter(prefix="/api")


# ---------- Static catalogue ----------

# Whole-menu items. `custom_box_unit` (optional) = per-piece price when included in a
# customer's custom box (small quantities). Items without it are only sold whole/by batch.
PRODUCTS = [
    # --- LOAVES (Serves 5–6) ---
    {
        "id": "apple-cinnamon-loaf",
        "name": "Apple Cinnamon Loaf",
        "category": "loaf",
        "price": 950,
        "serves": "5–6",
        "serves_min": 5,
        "serves_max": 6,
        "unit": "loaf",
        "moods": ["Warm & comforting"],
        "occasions": [
            "Tea party",
            "Family gathering",
            "Anniversary",
            "Just craving something",
        ],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790867603/IMG-20250824-WA0183.jpg",
        "story": "Warm, gentle spice and cinnamon — it makes the kitchen smell like a Sunday afternoon.",
    },
    {
        "id": "chocolate-chip-banana",
        "name": "Choco Chip Banana Bread",
        "category": "loaf",
        "price": 1200,
        "serves": "5–6",
        "serves_min": 5,
        "serves_max": 6,
        "unit": "loaf",
        "addons": [{"name": "Walnuts", "price": 100}],
        "moods": ["Warm & comforting", "Chocolate lover"],
        "occasions": [
            "Tea party",
            "Family gathering",
            "Just craving something",
            "Birthday",
        ],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790870752/image_6ac914dd.jpg",
        "story": "The loaf you slice on a slow Sunday, with chocolate melting into every crumb.",
    },
    {
        "id": "lemon-loaf",
        "name": "Lemon Loaf",
        "category": "loaf",
        "price": 1200,
        "serves": "5–6",
        "serves_min": 5,
        "serves_max": 6,
        "unit": "loaf",
        "moods": ["Fresh & citrusy", "Warm & comforting"],
        "occasions": [
            "Tea party",
            "Gift",
            "Family gathering",
            "Just craving something",
        ],
        "image": "https://images.unsplash.com/photo-1519869325930-281384150729?auto=format&fit=crop&w=900&q=85",
        "story": "Bright lemon zest folded into a tender crumb and drizzled with a sweet citrus glaze.",
    },
    {
        "id": "coconut-loaf",
        "name": "Coconut Loaf",
        "category": "loaf",
        "price": 1200,
        "serves": "5–6",
        "serves_min": 5,
        "serves_max": 6,
        "unit": "loaf",
        "moods": ["Something different", "Richly coconutty & subtly sweet"],
        "occasions": ["Tea party", "Gift", "Eid", "Anniversary"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790866286/IMG-20250821-WA0289.jpg",
        "story": "Toasted coconut, soft crumb, quiet luxury — the loaf that surprises everyone at the table.",
    },
    {
        "id": "coffee-walnut-loaf",
        "name": "Coffee Bread with Walnut Crumble",
        "category": "loaf",
        "price": 1200,
        "serves": "5–6",
        "serves_min": 5,
        "serves_max": 6,
        "unit": "loaf",
        "moods": ["Coffee lover", "Warm & comforting"],
        "occasions": ["Anniversary", "Family gathering", "Graduation", "Tea party"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790869322/image_6aeade9c_1.jpg",
        "story": "For the ones who take their afternoons with a strong cup and a slower conversation.",
    },
    {
        "id": "double-chocolate-loaf",
        "name": "Double Chocolate Loaf",
        "category": "loaf",
        "price": 1800,
        "serves": "5–6",
        "serves_min": 5,
        "serves_max": 6,
        "unit": "loaf",
        "moods": ["Chocolate lover", "Rich & indulgent"],
        "occasions": ["Birthday", "Gift", "Family gathering", "Just craving something"],
        "image": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=900&q=85",
        "story": "Deep, velvety cocoa crumb studded with molten chocolate chunks for the true devotee.",
    },
    {
        "id": "mini-loaves-batch",
        "name": "Mini Loaves (Pack of 4)",
        "category": "loaf",
        "price": 2000,
        "unit": "pack of 4",
        "pack_size": 4,
        "flavors": ["Lemon", "Coconut", "Coffee Walnut", "Double Chocolate"],
        "serves": "4",
        "serves_min": 4,
        "serves_max": 4,
        "moods": ["Something different", "Warm & comforting"],
        "occasions": ["Tea party", "Gift", "Family gathering", "Just craving something"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790870245/image_33e1256e.jpg",
        "story": "Four adorable mini loaves — mix any combination of Lemon, Coconut, Coffee Walnut, or Double Chocolate.",
    },
    # --- HEALTHY RANGE ---
    {
        "id": "sugar-free-dates",
        "name": "Sugar-Free Dates Loaf",
        "category": "loaf",
        "price": 1800,
        "serves": "5–6",
        "serves_min": 5,
        "serves_max": 6,
        "unit": "loaf",
        "healthy": True,
        "note": "with walnuts & chocolate chips",
        "moods": ["Warm & comforting", "Something different"],
        "occasions": ["Gift", "Family gathering", "Just craving something"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790869786/image_8402ea07.jpg",
        "story": "Naturally sweet with Arabian dates and walnuts — the loaf you bring for mindful indulgence.",
    },
    {
        "id": "oat-flour-banana-bread",
        "name": "Oat Flour Choco Chip Banana Bread",
        "category": "loaf",
        "price": 1200,
        "serves": "5–6",
        "serves_min": 5,
        "serves_max": 6,
        "unit": "loaf",
        "healthy": True,
        "note": "Wholesome oat flour & dark chocolate",
        "moods": ["Warm & comforting", "Chocolate lover"],
        "occasions": ["Tea party", "Family gathering", "Just craving something"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790870752/image_6ac914dd.jpg",
        "story": "Wholesome oat flour, ripe sweet bananas, and rich chocolate chips baked to golden perfection.",
    },
    {
        "id": "flourless-brownies",
        "name": "Flourless Brownies (Box of 4)",
        "category": "batch",
        "price": 1200,
        "unit": "box of 4",
        "batch_size": 4,
        "pack_size": 4,
        "flavors": ["Flourless Fudgy"],
        "custom_box_unit": 300,
        "healthy": True,
        "note": "Gluten-free & intensely chocolatey",
        "moods": ["Chocolate lover", "Rich & indulgent"],
        "occasions": ["Gift", "Birthday", "Just craving something"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790867082/image_89afef93.jpg",
        "story": "Incredibly fudgy and rich without a speck of flour — gluten-friendly comfort at its finest.",
    },
    {
        "id": "oat-flour-cookie",
        "name": "Oat Flour Chocolate Chip Cookie",
        "category": "cookie",
        "price": 400,
        "unit": "piece",
        "custom_box_unit": 400,
        "healthy": True,
        "note": "Nutrient-rich & hearty crunch",
        "moods": ["Warm & comforting", "Chocolate lover"],
        "occasions": ["Gift", "Just craving something"],
        "image": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&w=900&q=85",
        "story": "Hearty rolled oat flour studded with melted chocolate chips — crisp edges with a soft, chewy center.",
    },
    # --- BROWNIES & BAKES ---
    {
        "id": "brownies-batch",
        "name": "Brownies (Box of 4)",
        "category": "batch",
        "price": 1200,
        "unit": "box of 4",
        "batch_size": 4,
        "pack_size": 4,
        "flavors": ["Classic Fudgy", "Walnut Fudge", "Flourless"],
        "custom_box_unit": 300,
        "moods": ["Chocolate lover"],
        "occasions": ["Gift", "Just craving something", "Birthday"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790867082/image_89afef93.jpg",
        "story": "Dense, crinkly-topped and intensely fudgy. Pick any mix of Classic, Walnut Fudge, and Flourless.",
    },
    {
        "id": "cinnamon-rolls-batch",
        "name": "Cinnamon Rolls (Pack of 4)",
        "category": "batch",
        "price": 1600,
        "unit": "pack of 4",
        "batch_size": 4,
        "pack_size": 4,
        "flavors": ["Chocolate", "Vanilla"],
        "custom_box_unit": 400,
        "moods": ["Warm & comforting"],
        "occasions": ["Tea party", "Family gathering", "Baby born", "Gift"],
        "image": "https://images.unsplash.com/photo-1694632288834-17d86b340745?auto=format&fit=crop&w=900&q=85",
        "story": "Soft brioche spirals warmly spiced with Ceylon cinnamon. Choose any ratio of Chocolate and Vanilla glaze.",
    },
    {
        "id": "papparoti-batch",
        "name": "Papparoti Buns (Box of 4)",
        "category": "batch",
        "price": 1200,
        "unit": "box of 4",
        "batch_size": 4,
        "pack_size": 4,
        "flavors": ["Classic Coffee Crust"],
        "custom_box_unit": 300,
        "moods": ["Coffee lover", "Warm & comforting"],
        "occasions": ["Tea party", "Just craving something"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790938012/IMG-20261002-WA0137.jpg",
        "story": "Golden, buttery buns blanketed under a crisp, fragrant coffee caramel crust.",
    },
    # --- DESSERT CUPS ---
    {
        "id": "mango-trifle",
        "name": "Mango Trifle Cup",
        "category": "batch",
        "price": 350,
        "serves": "1",
        "serves_min": 1,
        "serves_max": 1,
        "unit": "cup",
        "custom_box_unit": 350,
        "moods": ["Fresh & creamy"],
        "occasions": ["Tea party", "Gift", "Baby born", "Just craving something"],
        "image": "https://res.cloudinary.com/dffsqfwok/image/upload/w_900,q_auto,f_auto/v1790760596/Mango_dessert_trays_on_surface_2K_20260930142859_zpcb6w.jpg",
        "story": "Layers of moist sponge, fresh sweet mango puree, and delicate velvety custard cream.",
    },
    {
        "id": "chocolate-trifle",
        "name": "Chocolate Trifle Cup",
        "category": "batch",
        "price": 400,
        "serves": "1",
        "serves_min": 1,
        "serves_max": 1,
        "unit": "cup",
        "custom_box_unit": 400,
        "moods": ["Rich & indulgent", "Chocolate lover"],
        "occasions": ["Tea party", "Gift", "Baby born", "Just craving something"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790867380/ChatGPT_Image_Jun_13_2026_12_23_46_AM.png",
        "story": "Layers of rich chocolate sponge, silky mousse, and chocolate shavings in every spoonful.",
    },
    {
        "id": "malt-cake",
        "name": "Malt Cake Cup",
        "category": "batch",
        "price": 400,
        "serves": "1",
        "serves_min": 1,
        "serves_max": 1,
        "unit": "cup",
        "custom_box_unit": 400,
        "moods": ["Chocolate lover", "Something different"],
        "occasions": ["Gift", "Just craving something"],
        "image": "https://images.unsplash.com/photo-1621939514649-280e2ee25f60?auto=format&fit=crop&w=900&q=85",
        "story": "Old-fashioned malted chocolate cake topped with a fluffy malt glaze in a cute individual cup.",
    },
    {
        "id": "dessert-cups-pack-4",
        "name": "Dessert Cups (Pack of 4)",
        "category": "batch",
        "price": 1500,
        "unit": "pack of 4",
        "pack_size": 4,
        "flavors": ["Mango Trifle", "Chocolate Trifle", "Malt Cake"],
        "serves": "4",
        "serves_min": 4,
        "serves_max": 4,
        "moods": ["Fresh & creamy", "Chocolate lover"],
        "occasions": ["Tea party", "Gift", "Family gathering"],
        "image": "https://res.cloudinary.com/dffsqfwok/image/upload/w_900,q_auto,f_auto/v1790760596/Mango_dessert_trays_on_surface_2K_20260930142859_zpcb6w.jpg",
        "story": "Four individual dessert cups — mix and match Mango Trifle, Chocolate Trifle, or Malt Cake in any combination.",
    },
    # --- COOKIES ---
    {
        "id": "chocolate-chip-cookie",
        "name": "Chocolate Chip Cookie",
        "category": "cookie",
        "price": 300,
        "unit": "piece",
        "custom_box_unit": 300,
        "moods": ["Chocolate lover", "Warm & comforting"],
        "occasions": ["Gift", "Just craving something"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790937990/IMG-20261002-WA0186.jpg",
        "story": "The cookie that behaves — golden crisp on the outer rim, gooey chocolate pooled inside.",
    },
    {
        "id": "double-chocolate-cookie",
        "name": "Double Chocolate Cookie",
        "category": "cookie",
        "price": 350,
        "unit": "piece",
        "custom_box_unit": 350,
        "moods": ["Chocolate lover"],
        "occasions": ["Gift", "Birthday", "Just craving something"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790938869/IMG-20261002-WA0190.jpg",
        "story": "Pure chocolate cookie dough crammed with milk and semi-sweet chocolate pockets.",
    },
    {
        "id": "cookies-pack-4",
        "name": "Cookies (Pack of 4)",
        "category": "cookie",
        "price": 1200,
        "unit": "pack of 4",
        "pack_size": 4,
        "flavors": ["Chocolate Chip", "Double Chocolate", "Oat Flour Chocolate Chip"],
        "moods": ["Chocolate lover", "Warm & comforting"],
        "occasions": ["Gift", "Birthday", "Family gathering"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790937990/IMG-20261002-WA0186.jpg",
        "story": "Four freshly baked artisanal cookies — pick your 4 favourite cookies in any combination.",
    },
    # --- CHEESECAKE & DESSERT BOXES ---
    {
        "id": "nyc-cheesecake",
        "name": "New York Cheesecake",
        "category": "cheesecake",
        "price": 2200,
        "unit": "1 lb",
        "serves": "6–8",
        "serves_min": 6,
        "serves_max": 8,
        "variants": ["Strawberry Topping", "Lemon Topping"],
        "moods": ["Fresh & citrusy", "Something different"],
        "occasions": ["Anniversary", "Birthday", "Gift"],
        "image": "https://res.cloudinary.com/n9pu62pg/image/upload/v1790867632/IMG-20250913-WA0191.jpg",
        "story": "Slow-baked, silky New York style cheesecake on a buttery biscuit crust. Comes with your choice of Strawberry or Lemon topping.",
    },
    {
        "id": "pineapple-cheesecake",
        "name": "Pineapple Dessert Box",
        "category": "cheesecake",
        "price": 1800,
        "unit": "1 lb",
        "serves": "6–8",
        "serves_min": 6,
        "serves_max": 8,
        "moods": ["Fresh & citrusy", "Something different"],
        "occasions": ["Tea party", "Gift", "Family gathering"],
        "image": "https://images.unsplash.com/photo-1587411768638-ec71f8e33b78?auto=format&fit=crop&w=900&q=85",
        "story": "Bright tropical pineapple chunks against a light, pillowy cream cheese filling.",
    },
    {
        "id": "banoffee-pie",
        "name": "Banoffee Pie Trifle Box",
        "category": "cheesecake",
        "price": 2100,
        "unit": "1 box",
        "serves": "6–8",
        "serves_min": 6,
        "serves_max": 8,
        "moods": ["Warm & comforting", "Chocolate lover"],
        "occasions": ["Family gathering", "Anniversary", "Gift"],
        "image": "https://images.unsplash.com/photo-1568827999250-3f6afff96e66?auto=format&fit=crop&w=900&q=85",
        "story": "Rich dulce de leche toffee, fresh sliced bananas, and clouds of coffee-dusted whipped cream.",
    },
    {
        "id": "coffee-cake-nutty",
        "name": "Coffee Cake with Nutty Brittle",
        "category": "cheesecake",
        "price": 1200,
        "unit": "1 lb",
        "serves": "5–6",
        "serves_min": 5,
        "serves_max": 6,
        "moods": ["Coffee lover"],
        "occasions": ["Tea party", "Anniversary", "Graduation"],
        "image": "https://images.unsplash.com/photo-1571115177098-24ec42ed204d?auto=format&fit=crop&w=900&q=85",
        "story": "Deep roast coffee crumb frosted with brown butter buttercream and crowned with caramelized nut brittle.",
    },
    {
        "id": "fruit-trifle-box",
        "name": "Fruit Trifle Box",
        "category": "cheesecake",
        "price": 1800,
        "unit": "1 box",
        "serves": "6–8",
        "serves_min": 6,
        "serves_max": 8,
        "moods": ["Fresh & creamy"],
        "occasions": ["Family gathering", "Eid", "Tea party"],
        "image": "https://res.cloudinary.com/dffsqfwok/image/upload/w_900,q_auto,f_auto/v1790760596/Mango_dessert_trays_on_surface_2K_20260930142859_zpcb6w.jpg",
        "story": "Generous party box layered with golden sponge, fresh seasonal fruit medley, and silky homemade custard.",
    },
    {
        "id": "salted-caramel-brownie-trifle",
        "name": "Salted Caramel Brownie Trifle Box",
        "category": "cheesecake",
        "price": 2500,
        "unit": "1 box",
        "serves": "6–8",
        "serves_min": 6,
        "serves_max": 8,
        "moods": ["Rich & indulgent", "Chocolate lover"],
        "occasions": ["Anniversary", "Birthday", "Gift"],
        "image": "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?auto=format&fit=crop&w=900&q=85",
        "story": "Fudgy brownie bites, housemade golden salted caramel, and chantilly cream in an indulgent party tray.",
    },
    {
        "id": "malt-cake-box",
        "name": "Malt Cake Box",
        "category": "cheesecake",
        "price": 1800,
        "unit": "1 box",
        "serves": "6–8",
        "serves_min": 6,
        "serves_max": 8,
        "moods": ["Chocolate lover", "Something different"],
        "occasions": ["Birthday", "Family gathering", "Gift"],
        "image": "https://images.unsplash.com/photo-1621939514649-280e2ee25f60?auto=format&fit=crop&w=900&q=85",
        "story": "Tender chocolate malt cake generously frosted with our signature malt fudge frosting.",
    },
]


PACKAGING = [
    {
        "id": "clear-box",
        "name": "Clear Plastic Box with Pink Ribbon",
        "price": 150,
        "ribbon": "pink",
        "style": "clear",
        "image": "https://customer-assets-rejwkqb3.emergentagent.net/job_bake-moment/artifacts/byzd23k4_2981-Pastry-Box-9-x-6.webp",
    },
    {
        "id": "white-box",
        "name": "White Cardboard Box with Pink Ribbon",
        "price": 150,
        "ribbon": "pink",
        "style": "white",
        "image": "https://customer-assets-rejwkqb3.emergentagent.net/job_bake-moment/artifacts/ww1p99rw_2666-Brownie-Box-6x6x2.webp",
    },
    {
        "id": "kraft-box",
        "name": "Brown Kraft Box with Pink Ribbon",
        "price": 150,
        "ribbon": "pink",
        "style": "kraft",
        "image": "https://customer-assets-rejwkqb3.emergentagent.net/job_bake-moment/artifacts/98od3myz_2666-1-Brownie-Box-6-x-6-x-2-4-Pcs-.webp",
    },
]


FESTIVE_BOXES = [
    {
        "id": "anniversary-box",
        "name": "Anniversary Box",
        "tagline": "Slow, warm and a little bit romantic.",
        "items": [
            {"product_id": "coffee-walnut-loaf", "qty": 1},
            {"product_id": "cinnamon-rolls-batch", "qty": 1},
        ],
        "image": "https://res.cloudinary.com/dffsqfwok/image/upload/v1790781186/Bakery_gift_box_product_shoot_2K_20260930201127_tpv8bt.jpg?pid=1617118601021",
    },
    {
        "id": "birthday-box",
        "name": "Birthday Box",
        "tagline": "The loud, chocolatey kind of joy.",
        "items": [
            {"product_id": "chocolate-chip-banana", "qty": 1},
            {"product_id": "brownies-batch", "qty": 1},
            {"product_id": "double-chocolate-loaf", "qty": 1},
        ],
        "image": "https://res.cloudinary.com/dffsqfwok/image/upload/v1790781445/Bakery_product_shoot_for_website_2K_20260930201702_wr1y0v.jpg?pid=1700045530510",
    },
    {
        "id": "graduation-box",
        "name": "Graduation Box",
        "tagline": "A proud, celebratory afternoon.",
        "items": [
            {"product_id": "coffee-walnut-loaf", "qty": 1},
            {"product_id": "cinnamon-rolls-batch", "qty": 1},
        ],
        "image": "https://res.cloudinary.com/dffsqfwok/image/upload/v1790781742/Graduation_pastry_gift_box_shoot_2K_20260930202204_uatomr.jpg?pid=1764385827123",
    },
    {
        "id": "eid-box",
        "name": "Eid Box",
        "tagline": "Sweet, generous and made for sharing.",
        "items": [
            {"product_id": "coconut-loaf", "qty": 1},
            {"product_id": "double-chocolate-cookie", "qty": 4},
            {"product_id": "papparoti-batch", "qty": 1},
        ],
        "image": "https://res.cloudinary.com/dffsqfwok/image/upload/v1790782194/Eid_dessert_box_product_shoot_2K_20260930202830_gn5gmr.jpg?pid=1513201099705",
    },
    {
        "id": "baby-born-box",
        "name": "Baby Born Box",
        "tagline": "Gentle, bright and full of good wishes.",
        "items": [
            {"product_id": "mango-trifle", "qty": 3},
            {"product_id": "chocolate-trifle", "qty": 3},
        ],
        "image": "https://res.cloudinary.com/dffsqfwok/image/upload/v1790782197/Designing_baby_dessert_gift_box_2K_20260930202937_vsh6nh.jpg?pid=1700045530510",
    },
]


def _by_id():
    return {p["id"]: p for p in PRODUCTS}


def _pack_by_id():
    return {p["id"]: p for p in PACKAGING}


def _hydrate_box(box):
    pmap = _by_id()
    items = []
    total = 0
    for it in box["items"]:
        p = pmap.get(it["product_id"])
        if not p:
            continue
        items.append({"product": p, "qty": it["qty"]})
        total += p["price"] * it["qty"]
    return {**box, "items": items, "total": total}


# ---------- Models ----------


class MatchRequest(BaseModel):
    occasion: str
    mood: str
    people: int
    budget: int
    dietary: str = "No preference"


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class SaveMatchRequest(BaseModel):
    product_id: str
    occasion: str
    mood: str
    people: int
    budget: int
    dietary: str = "No preference"
    explanation: str


class OrderItem(BaseModel):
    product_id: str
    qty: int = Field(ge=1, le=99)
    # When True, use custom_box_unit price instead of the full/batch price.
    custom_box: bool = False
    selected_variant: Optional[str] = None
    pack_selection: Optional[dict[str, int]] = None


class Customer(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=6, max_length=30)
    address: str = Field(min_length=4, max_length=400)
    delivery_date: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class CreateOrderRequest(BaseModel):
    items: List[OrderItem]
    packaging_id: Optional[str] = None
    personalized_message: Optional[str] = Field(default=None, max_length=140)
    customer: Customer


# ---------- Matchmaker (loaves only — the emotional layer) ----------

LOAF_CATALOGUE_FOR_AI = [
    {
        "name": p["name"],
        "price": p["price"],
        "serves": p["serves"],
        "moods": p["moods"],
        "occasions": p["occasions"],
    }
    for p in PRODUCTS
    if p["category"] == "loaf"
]

FULL_CATALOGUE_FOR_AI = [
    {
        "name": p["name"],
        "price": p["price"],
        "unit": p.get("unit", "each"),
        "moods": p["moods"],
        "occasions": p["occasions"],
    }
    for p in PRODUCTS
]


def _score(product, req: MatchRequest):
    if product["category"] != "loaf":
        return -1e9
    score = 0
    if req.mood in product["moods"]:
        score += 3
    if req.occasion in product["occasions"]:
        score += 3
    if product["price"] <= req.budget:
        score += 2
    mid = (product["serves_min"] + product["serves_max"]) / 2
    score -= abs(mid - req.people) * 0.1
    if product["price"] > req.budget:
        score -= (product["price"] - req.budget) / 200
    if req.dietary.lower().startswith("less sweet") or "sugar" in req.dietary.lower():
        if product.get("healthy"):
            score += 4
    return score


def _pick_product(req: MatchRequest):
    return max(PRODUCTS, key=lambda p: _score(p, req))


async def ask_baker(
    prompt: str, session_id: str, system_extra: str = "", full_catalogue: bool = True
):
    key = os.environ.get("EMERGENT_LLM_KEY") or os.environ.get("OPENAI_API_KEY")
    catalogue = FULL_CATALOGUE_FOR_AI if full_catalogue else LOAF_CATALOGUE_FOR_AI
    system_message = (
        "You are the warm, concise home baker for Treats & Temptation by SK. "
        "Only ever mention items from this catalogue (never invent products, prices or ingredients): "
        + json.dumps(catalogue)
        + ". "
        "Speak like a friend, not a menu. Keep replies under 90 words. All prices are in Rs."
    )
    if system_extra:
        system_message += " " + system_extra

    if not key:
        raise ValueError("No LLM API key provided")

    # 1. Native Emergent environment support
    if LlmChat and os.environ.get("EMERGENT_LLM_KEY"):
        chat = LlmChat(
            api_key=key, session_id=session_id, system_message=system_message
        ).with_model("openai", "gpt-4o-mini")
        text = ""
        async for event in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(event, TextDelta):
                text += event.content
            elif isinstance(event, StreamDone):
                break
        return text.strip()

    # 2. Local / Standard OpenAI fallback
    from openai import AsyncOpenAI

    openai_client = AsyncOpenAI(api_key=key, timeout=3.0)
    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


# ---------- Routes ----------


@api_router.get("/")
async def root():
    return {"message": "Treats & Temptation by SK API"}


@api_router.get("/products")
async def list_products():
    return PRODUCTS


@api_router.get("/packaging")
async def list_packaging():
    return PACKAGING


@api_router.get("/festive-boxes")
async def list_festive_boxes():
    return [_hydrate_box(b) for b in FESTIVE_BOXES]


@api_router.get("/festive-boxes/{box_id}")
async def get_festive_box(box_id: str):
    for b in FESTIVE_BOXES:
        if b["id"] == box_id:
            return _hydrate_box(b)
    raise HTTPException(status_code=404, detail="Festive box not found")


@api_router.post("/match")
async def match_dessert(request: MatchRequest):
    best = _pick_product(request)
    prompt = (
        f"The perfect loaf for this customer is: {best['name']} (Rs. {best['price']}, serves {best['serves']}). "
        f"They are buying for a {request.occasion.lower()}, in the mood for {request.mood.lower()}, "
        f"for {request.people} people, budget around Rs. {request.budget}, dietary: {request.dietary}. "
        f"Write ONE warm, personal sentence (max 30 words) explaining why {best['name']} suits them. "
        f"You MUST use the exact name '{best['name']}' and MUST NOT mention any other loaf or bake."
    )
    try:
        explanation = await ask_baker(
            prompt,
            "match-" + uuid.uuid4().hex,
            system_extra=f"For this reply you must only talk about '{best['name']}'.",
            full_catalogue=False,
        )
    except Exception as e:
        logging.getLogger(__name__).warning("match LLM error: %s", e)
        explanation = f"{best['name']} feels just right — warm, homemade, and made for the moment you're planning."
    other_names = [
        p["name"] for p in PRODUCTS if p["category"] == "loaf" and p["id"] != best["id"]
    ]
    if best["name"].lower() not in explanation.lower() or any(
        n.lower() in explanation.lower() for n in other_names
    ):
        explanation = f"{best['name']} — a warm, homemade pick for your {request.occasion.lower()}. Perfect for {request.people} and stays gently within your Rs. {request.budget} budget."
    return {"product": best, "explanation": explanation}


IN_MEMORY_MATCHES = {}
IN_MEMORY_ORDERS = {}


@api_router.post("/match/save")
async def save_match(payload: SaveMatchRequest):
    pmap = _by_id()
    if payload.product_id not in pmap:
        raise HTTPException(status_code=404, detail="Unknown product")
    match_id = uuid.uuid4().hex[:10]
    match_doc = {
        "match_id": match_id,
        "product_id": payload.product_id,
        "occasion": payload.occasion,
        "mood": payload.mood,
        "people": payload.people,
        "budget": payload.budget,
        "dietary": payload.dietary,
        "explanation": payload.explanation,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    IN_MEMORY_MATCHES[match_id] = match_doc
    try:
        await db.saved_matches.insert_one(match_doc)
    except Exception as e:
        logging.getLogger(__name__).warning("MongoDB save_match fallback to in-memory: %s", e)
    return {"id": match_id}


@api_router.get("/match/{match_id}")
async def get_saved_match(match_id: str):
    doc = None
    try:
        doc = await db.saved_matches.find_one({"match_id": match_id}, {"_id": 0})
    except Exception:
        pass
    if not doc:
        doc = IN_MEMORY_MATCHES.get(match_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Match not found")
    product = _by_id().get(doc["product_id"])
    if not product:
        raise HTTPException(status_code=404, detail="Match no longer available")
    return {
        "id": doc["match_id"],
        "product": product,
        "explanation": doc["explanation"],
        "occasion": doc.get("occasion"),
        "mood": doc.get("mood"),
        "people": doc.get("people"),
        "budget": doc.get("budget"),
    }


@api_router.post("/chat")
async def baker_chat(request: ChatRequest):
    session_id = request.session_id or "chat-" + uuid.uuid4().hex
    try:
        reply = await ask_baker(request.message, session_id, full_catalogue=True)
        ok = True
    except Exception as e:
        logging.getLogger(__name__).warning("chat LLM error: %s", e)
        reply = "The oven's a little warm right now — try me again in a moment."
        ok = False
    try:
        await db.baker_chats.insert_one(
            {
                "session_id": session_id,
                "message": request.message,
                "reply": reply,
                "ok": ok,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception:
        pass
    return {"session_id": session_id, "reply": reply, "ok": ok}


def _new_order_number():
    return "TT" + "".join(random.choices("0123456789", k=6))


@api_router.post("/orders")
async def create_order(payload: CreateOrderRequest):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    pmap = _by_id()
    packmap = _pack_by_id()

    lines = []
    subtotal = 0
    for item in payload.items:
        product = pmap.get(item.product_id)
        if not product:
            raise HTTPException(
                status_code=404, detail=f"Unknown product: {item.product_id}"
            )
        if item.custom_box and "custom_box_unit" not in product:
            raise HTTPException(
                status_code=400,
                detail=f"{product['name']} is not sold as a custom-box unit",
            )

        # Validate variant if provided
        if item.selected_variant and product.get("variants"):
            if item.selected_variant not in product["variants"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid variant '{item.selected_variant}' for {product['name']}. Available: {product['variants']}",
                )

        # Validate pack selection if provided
        if item.pack_selection:
            pack_size = product.get("pack_size", 4)
            count = sum(item.pack_selection.values())
            if count != pack_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"{product['name']} requires exactly {pack_size} items selected (got {count})",
                )
            if product.get("flavors"):
                for flavor in item.pack_selection.keys():
                    if flavor not in product["flavors"]:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid flavor '{flavor}' for {product['name']}. Available: {product['flavors']}",
                        )

        unit_price = product["custom_box_unit"] if item.custom_box else product["price"]
        line_total = unit_price * item.qty
        subtotal += line_total
        lines.append(
            {
                "product_id": product["id"],
                "name": product["name"],
                "qty": item.qty,
                "custom_box": item.custom_box,
                "selected_variant": item.selected_variant,
                "pack_selection": item.pack_selection,
                "unit_price": unit_price,
                "line_total": line_total,
                "image": product["image"],
            }
        )

    pack = None
    packaging_total = 0
    if payload.packaging_id:
        pack = packmap.get(payload.packaging_id)
        if not pack:
            raise HTTPException(status_code=404, detail="Unknown packaging option")
        packaging_total = pack["price"]

    total = subtotal + packaging_total
    order_number = _new_order_number()

    order_doc = {
        "order_number": order_number,
        "items": lines,
        "packaging": (
            {
                "id": pack["id"],
                "name": pack["name"],
                "price": pack["price"],
                "ribbon": pack["ribbon"],
                "style": pack.get("style"),
                "image": pack.get("image"),
            }
            if pack
            else None
        ),
        "personalized_message": payload.personalized_message or "",
        "customer": payload.customer.model_dump(),
        "subtotal": subtotal,
        "packaging_total": packaging_total,
        "total": total,
        "currency": "PKR",
        "status": "pending_confirmation",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    IN_MEMORY_ORDERS[order_number] = dict(order_doc)
    try:
        await db.orders.insert_one(order_doc)
    except Exception as e:
        logging.getLogger(__name__).warning("MongoDB create_order fallback to in-memory: %s", e)
    order_doc.pop("_id", None)
    return order_doc


@api_router.get("/orders/{order_number}")
async def get_order(order_number: str):
    doc = None
    try:
        doc = await db.orders.find_one({"order_number": order_number}, {"_id": 0})
    except Exception:
        pass
    if not doc:
        doc = IN_MEMORY_ORDERS.get(order_number)
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    return doc


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
