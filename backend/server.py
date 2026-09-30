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
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")


# ---------- Static catalogue ----------

# Whole-menu items. `custom_box_unit` (optional) = per-piece price when included in a
# customer's custom box (small quantities). Items without it are only sold whole/by batch.
PRODUCTS = [
    # Loaves (whole, ~6-8 people)
    {"id": "lemon-loaf", "name": "Mango Trifle Cups", "category": "loaf", "price": 850, "serves": "6–8",
     "serves_min": 6, "serves_max": 8, "unit": "loaf",
     "moods": ["Fresh & citrusy"], "occasions": ["Tea party", "Gift", "Baby born", "Just craving something"],
     "image": "https://res.cloudinary.com/dffsqfwok/image/upload/v1790760596/Mango_dessert_trays_on_surface_2K_20260930142859_zpcb6w.jpg",
     "story": "Bright, sunlit slices for the mornings that need a lift and the afternoons that need a smile."},
    {"id": "chocolate-chip-banana", "name": "Chocolate Chip Banana Bread", "category": "loaf", "price": 900,
     "serves": "6–8", "serves_min": 6, "serves_max": 8, "unit": "loaf",
     "addons": [{"name": "Walnuts", "price": 100}],
     "moods": ["Warm & comforting", "Chocolate lover"], "occasions": ["Tea party", "Family gathering", "Just craving something", "Birthday"],
     "image": "https://images.unsplash.com/photo-1621994214182-f467e6999dc9?auto=format&fit=crop&w=900&q=85",
     "story": "The loaf you slice on a slow Sunday, with chocolate melting into every crumb."},
    {"id": "apple-cinnamon-loaf", "name": "Cinnamon Rolls", "category": "loaf", "price": 850,
     "serves": "6–8", "serves_min": 6, "serves_max": 8, "unit": "loaf",
     "moods": ["Warm & comforting"], "occasions": ["Tea party", "Family gathering", "Anniversary", "Just craving something"],
     "image": "https://images.unsplash.com/photo-1509365465985-25d11c17e812?auto=format&fit=crop&w=900&q=85",
     "story": "Warm, gentle spice and cinnamon — it makes the kitchen smell like a Sunday afternoon."},
    {"id": "coffee-walnut-loaf", "name": "Coffee Bread with Walnut Crumble", "category": "loaf", "price": 1200,
     "serves": "6–8", "serves_min": 6, "serves_max": 8, "unit": "loaf",
     "moods": ["Coffee lover", "Warm & comforting"], "occasions": ["Anniversary", "Family gathering", "Graduation", "Tea party"],
     "image": "https://images.unsplash.com/photo-1571115177098-24ec42ed204d?auto=format&fit=crop&w=900&q=85",
     "story": "For the ones who take their afternoons with a strong cup and a slower conversation."},
    {"id": "coconut-loaf", "name": "Coconut Loaf", "category": "loaf", "price": 1200,
     "serves": "6–8", "serves_min": 6, "serves_max": 8, "unit": "loaf",
     "moods": ["Something different", "Fresh & citrusy"], "occasions": ["Tea party", "Gift", "Eid", "Anniversary"],
     "image": "https://images.unsplash.com/photo-1568051243851-f9b136146e97?auto=format&fit=crop&w=900&q=85",
     "story": "Toasted coconut, soft crumb, quiet luxury — the loaf that surprises everyone at the table."},
    {"id": "sugar-free-dates", "name": "Sugar-Free Dates Loaf", "category": "loaf", "price": 1800,
     "serves": "6–8", "serves_min": 6, "serves_max": 8, "unit": "loaf",
     "healthy": True, "note": "with walnuts & chocolate chips",
     "moods": ["Warm & comforting", "Something different"], "occasions": ["Gift", "Family gathering", "Just craving something"],
     "image": "https://images.unsplash.com/photo-1610450949065-1f2841536c88?auto=format&fit=crop&w=900&q=85",
     "story": "Naturally sweet, deeply nutty — the loaf you bring for the person watching their sugar."},

    # Cheesecakes & Desserts (1lb whole)
    {"id": "nyc-cheesecake", "name": "New York Cheesecake", "category": "cheesecake", "price": 2200,
     "unit": "1 lb", "serves": "6–8", "serves_min": 6, "serves_max": 8,
     "variants": ["Strawberry Sauce", "Lemon Sauce"],
     "moods": ["Fresh & citrusy", "Something different"], "occasions": ["Anniversary", "Birthday", "Gift"],
     "image": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=900&q=85",
     "story": "Slow-baked, gently vanilla, and quietly show-stopping."},
    {"id": "lotus-cheesecake", "name": "Lotus Cheesecake", "category": "cheesecake", "price": 2500,
     "unit": "1 lb", "serves": "6–8", "serves_min": 6, "serves_max": 8,
     "moods": ["Chocolate lover", "Something different"], "occasions": ["Birthday", "Anniversary", "Gift"],
     "image": "https://images.unsplash.com/photo-1567327613485-fbc7bf196198?auto=format&fit=crop&w=900&q=85",
     "story": "Caramelised biscoff, silky centre, the dessert nobody expects to fight over."},
    {"id": "pineapple-cheesecake", "name": "Pineapple Cheesecake Dessert Box", "category": "cheesecake", "price": 1800,
     "unit": "1 lb", "serves": "6–8", "serves_min": 6, "serves_max": 8,
     "moods": ["Fresh & citrusy", "Something different"], "occasions": ["Tea party", "Gift", "Family gathering"],
     "image": "https://images.unsplash.com/photo-1587411768638-ec71f8e33b78?auto=format&fit=crop&w=900&q=85",
     "story": "Bright pineapple against a soft cheesecake — a hot-weather kind of joy."},
    {"id": "banoffee-pie", "name": "Banoffee Pie", "category": "cheesecake", "price": 2100,
     "unit": "1 pie", "serves": "6–8", "serves_min": 6, "serves_max": 8,
     "moods": ["Warm & comforting", "Chocolate lover"], "occasions": ["Family gathering", "Anniversary", "Gift"],
     "image": "https://images.unsplash.com/photo-1568827999250-3f6afff96e66?auto=format&fit=crop&w=900&q=85",
     "story": "Toffee, banana and cream — the dessert your childhood is asking for."},
    {"id": "coffee-cake-nutty", "name": "Coffee Cake with Nutty Brittle", "category": "cheesecake", "price": 1200,
     "unit": "1 lb", "serves": "6–8", "serves_min": 6, "serves_max": 8,
     "moods": ["Coffee lover"], "occasions": ["Tea party", "Anniversary", "Graduation"],
     "image": "https://images.unsplash.com/photo-1571115177098-24ec42ed204d?auto=format&fit=crop&w=900&q=85",
     "story": "Coffee, brown butter, a shard of nutty brittle — grown-up in the best way."},

    # Batches
    {"id": "brownies-batch", "name": "Brownies", "category": "batch", "price": 1000,
     "unit": "batch of 4", "batch_size": 4, "custom_box_unit": 275,
     "moods": ["Chocolate lover"], "occasions": ["Gift", "Just craving something", "Birthday"],
     "image": "https://images.unsplash.com/photo-1642453031286-8991becafe19?auto=format&fit=crop&w=900&q=85",
     "story": "Dense, fudgy and gone before you remember to save one for later."},
    {"id": "cinnamon-rolls-batch", "name": "Cinnamon Rolls", "category": "batch", "price": 1400,
     "unit": "batch of 4", "batch_size": 4, "custom_box_unit": 375,
     "moods": ["Warm & comforting"], "occasions": ["Tea party", "Family gathering", "Baby born"],
     "image": "https://images.unsplash.com/photo-1694632288834-17d86b340745?auto=format&fit=crop&w=900&q=85",
     "story": "The box that makes an ordinary afternoon smell like a Sunday morning."},
    {"id": "papparoti-batch", "name": "Papparoti Buns", "category": "batch", "price": 800,
     "unit": "batch of 4", "batch_size": 4, "custom_box_unit": 225,
     "moods": ["Coffee lover", "Warm & comforting"], "occasions": ["Tea party", "Just craving something"],
     "image": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=900&q=85",
     "story": "Soft buns with a crackly coffee crust — best warm, with a strong cup."},
    {"id": "cadbury-eclair-batch", "name": "Cadbury Éclair Treat", "category": "batch", "price": 700,
     "unit": "batch of 3", "batch_size": 3, "custom_box_unit": 250,
     "moods": ["Chocolate lover", "Something different"], "occasions": ["Gift", "Just craving something"],
     "image": "https://images.unsplash.com/photo-1621939514649-280e2ee25f60?auto=format&fit=crop&w=900&q=85",
     "story": "The chocolate-cream classic, tucked into a treat-sized box."},

    # Cookies (per piece)
    {"id": "chocolate-chip-cookie", "name": "Chocolate Chip Cookie", "category": "cookie", "price": 200,
     "unit": "piece", "custom_box_unit": 200,
     "moods": ["Chocolate lover", "Warm & comforting"], "occasions": ["Gift", "Just craving something"],
     "image": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&w=900&q=85",
     "story": "The cookie that behaves — soft centre, crisp edges, chocolate everywhere."},
    {"id": "chocolate-filled-cookie", "name": "Chocolate Filled Cookie", "category": "cookie", "price": 250,
     "unit": "piece", "custom_box_unit": 250,
     "moods": ["Chocolate lover"], "occasions": ["Gift", "Just craving something", "Birthday"],
     "image": "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?auto=format&fit=crop&w=900&q=85",
     "story": "Break it in half — that's where the molten chocolate lives."},
    {"id": "lotus-cookie", "name": "Lotus Cookie", "category": "cookie", "price": 300,
     "unit": "piece", "custom_box_unit": 300,
     "moods": ["Something different"], "occasions": ["Gift", "Tea party"],
     "image": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=900&q=85",
     "story": "Caramelised, spiced and quietly obsessive — the biscoff lover's cookie."},
    {"id": "double-chocolate-cookie", "name": "Double Chocolate Cookie", "category": "cookie", "price": 300,
     "unit": "piece", "custom_box_unit": 300,
     "moods": ["Chocolate lover"], "occasions": ["Gift", "Birthday", "Just craving something"],
     "image": "https://images.unsplash.com/photo-1568051243851-f9b136146e97?auto=format&fit=crop&w=900&q=85",
     "story": "Chocolate cookie, chocolate chunks, no restraint."},
]


PACKAGING = [
    {"id": "clear-box", "name": "Clear Plastic Box with Pink Ribbon", "price": 150, "ribbon": "pink", "style": "clear",
     "image": "https://customer-assets-rejwkqb3.emergentagent.net/job_bake-moment/artifacts/byzd23k4_2981-Pastry-Box-9-x-6.webp"},
    {"id": "white-box", "name": "White Cardboard Box with Pink Ribbon", "price": 150, "ribbon": "pink", "style": "white",
     "image": "https://customer-assets-rejwkqb3.emergentagent.net/job_bake-moment/artifacts/ww1p99rw_2666-Brownie-Box-6x6x2.webp"},
    {"id": "kraft-box", "name": "Brown Kraft Box with Pink Ribbon", "price": 150, "ribbon": "pink", "style": "kraft",
     "image": "https://customer-assets-rejwkqb3.emergentagent.net/job_bake-moment/artifacts/98od3myz_2666-1-Brownie-Box-6-x-6-x-2-4-Pcs-.webp"},
]


FESTIVE_BOXES = [
    {"id": "anniversary-box", "name": "Anniversary Box", "tagline": "Slow, warm and a little bit romantic.",
     "items": [{"product_id": "coffee-walnut-loaf", "qty": 1}, {"product_id": "chocolate-filled-cookie", "qty": 4}],
     "image": "https://images.unsplash.com/photo-1617118601021-4992c028fe5d?auto=format&fit=crop&w=900&q=85"},
    {"id": "birthday-box", "name": "Birthday Box", "tagline": "The loud, chocolatey kind of joy.",
     "items": [{"product_id": "chocolate-chip-banana", "qty": 1}, {"product_id": "double-chocolate-cookie", "qty": 4}, {"product_id": "brownies-batch", "qty": 1}],
     "image": "https://images.unsplash.com/photo-1700045530510-6e03007a8f48?auto=format&fit=crop&w=900&q=85"},
    {"id": "graduation-box", "name": "Graduation Box", "tagline": "A proud, celebratory afternoon.",
     "items": [{"product_id": "coffee-walnut-loaf", "qty": 1}, {"product_id": "cinnamon-rolls-batch", "qty": 1}],
     "image": "https://images.unsplash.com/photo-1764385827123-45525c44373c?auto=format&fit=crop&w=900&q=85"},
    {"id": "eid-box", "name": "Eid Box", "tagline": "Sweet, generous and made for sharing.",
     "items": [{"product_id": "coconut-loaf", "qty": 1}, {"product_id": "lotus-cookie", "qty": 4}, {"product_id": "papparoti-batch", "qty": 1}],
     "image": "https://images.unsplash.com/photo-1513201099705-a9746e1e201f?auto=format&fit=crop&w=900&q=85"},
    {"id": "baby-born-box", "name": "Baby Born Box", "tagline": "Gentle, bright and full of good wishes.",
     "items": [{"product_id": "lemon-loaf", "qty": 1}, {"product_id": "cinnamon-rolls-batch", "qty": 1}],
     "image": "https://images.unsplash.com/photo-1700045530510-6e03007a8f48?auto=format&fit=crop&w=900&q=85"},
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
    {"name": p["name"], "price": p["price"], "serves": p["serves"], "moods": p["moods"], "occasions": p["occasions"]}
    for p in PRODUCTS if p["category"] == "loaf"
]

FULL_CATALOGUE_FOR_AI = [
    {"name": p["name"], "price": p["price"], "unit": p.get("unit", "each"), "moods": p["moods"], "occasions": p["occasions"]}
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


async def ask_baker(prompt: str, session_id: str, system_extra: str = "", full_catalogue: bool = True):
    key = os.environ["EMERGENT_LLM_KEY"]
    catalogue = FULL_CATALOGUE_FOR_AI if full_catalogue else LOAF_CATALOGUE_FOR_AI
    system_message = (
        "You are the warm, concise home baker for Treats & Temptation by SK. "
        "Only ever mention items from this catalogue (never invent products, prices or ingredients): "
        + json.dumps(catalogue) + ". "
        "Speak like a friend, not a menu. Keep replies under 90 words. All prices are in Rs."
    )
    if system_extra:
        system_message += " " + system_extra
    chat = LlmChat(api_key=key, session_id=session_id, system_message=system_message).with_model("openai", "gpt-4o-mini")
    text = ""
    async for event in chat.stream_message(UserMessage(text=prompt)):
        if isinstance(event, TextDelta):
            text += event.content
        elif isinstance(event, StreamDone):
            break
    return text.strip()


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
    other_names = [p["name"] for p in PRODUCTS if p["category"] == "loaf" and p["id"] != best["id"]]
    if best["name"].lower() not in explanation.lower() or any(n.lower() in explanation.lower() for n in other_names):
        explanation = f"{best['name']} — a warm, homemade pick for your {request.occasion.lower()}. Perfect for {request.people} and stays gently within your Rs. {request.budget} budget."
    return {"product": best, "explanation": explanation}


@api_router.post("/match/save")
async def save_match(payload: SaveMatchRequest):
    pmap = _by_id()
    if payload.product_id not in pmap:
        raise HTTPException(status_code=404, detail="Unknown product")
    match_id = uuid.uuid4().hex[:10]
    await db.saved_matches.insert_one({
        "match_id": match_id,
        "product_id": payload.product_id,
        "occasion": payload.occasion,
        "mood": payload.mood,
        "people": payload.people,
        "budget": payload.budget,
        "dietary": payload.dietary,
        "explanation": payload.explanation,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"id": match_id}


@api_router.get("/match/{match_id}")
async def get_saved_match(match_id: str):
    doc = await db.saved_matches.find_one({"match_id": match_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Match not found")
    product = _by_id().get(doc["product_id"])
    if not product:
        raise HTTPException(status_code=404, detail="Match no longer available")
    return {
        "id": doc["match_id"], "product": product, "explanation": doc["explanation"],
        "occasion": doc.get("occasion"), "mood": doc.get("mood"),
        "people": doc.get("people"), "budget": doc.get("budget"),
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
    await db.baker_chats.insert_one({
        "session_id": session_id, "message": request.message, "reply": reply, "ok": ok,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
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
            raise HTTPException(status_code=404, detail=f"Unknown product: {item.product_id}")
        if item.custom_box and "custom_box_unit" not in product:
            raise HTTPException(status_code=400, detail=f"{product['name']} is not sold as a custom-box unit")
        unit_price = product["custom_box_unit"] if item.custom_box else product["price"]
        line_total = unit_price * item.qty
        subtotal += line_total
        lines.append({
            "product_id": product["id"],
            "name": product["name"],
            "qty": item.qty,
            "custom_box": item.custom_box,
            "unit_price": unit_price,
            "line_total": line_total,
            "image": product["image"],
        })

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
        "packaging": ({"id": pack["id"], "name": pack["name"], "price": pack["price"], "ribbon": pack["ribbon"], "style": pack.get("style"), "image": pack.get("image")} if pack else None),
        "personalized_message": payload.personalized_message or "",
        "customer": payload.customer.model_dump(),
        "subtotal": subtotal,
        "packaging_total": packaging_total,
        "total": total,
        "currency": "PKR",
        "status": "pending_confirmation",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.orders.insert_one(order_doc)
    order_doc.pop("_id", None)
    return order_doc


@api_router.get("/orders/{order_number}")
async def get_order(order_number: str):
    doc = await db.orders.find_one({"order_number": order_number}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    return doc


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
