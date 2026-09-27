from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
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


class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


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


PRODUCTS = [
    {"id": "chocolate-chip-banana", "name": "Chocolate Chip Banana Bread", "price": 1200, "addons": [{"name": "Walnuts", "price": 100}],
     "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Warm & comforting", "Chocolate lover"], "occasions": ["Tea party", "Family gathering", "Just craving something", "Birthday"],
     "image": "https://images.unsplash.com/photo-1621994214182-f467e6999dc9?auto=format&fit=crop&w=900&q=85",
     "story": "The loaf you slice on a slow Sunday, with chocolate melting into every crumb."},
    {"id": "apple-cinnamon", "name": "Apple Cinnamon Loaf", "price": 950,
     "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Warm & comforting"], "occasions": ["Tea party", "Family gathering", "Just craving something", "Anniversary"],
     "image": "https://images.unsplash.com/photo-1509365465985-25d11c17e812?auto=format&fit=crop&w=900&q=85",
     "story": "Warm, gentle spice and soft apples — it makes the kitchen smell like a Sunday afternoon."},
    {"id": "lemon-loaf", "name": "Lemon Loaf", "price": 1200,
     "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Fresh & citrusy"], "occasions": ["Tea party", "Gift", "Baby born", "Just craving something"],
     "image": "https://images.unsplash.com/photo-1519915028121-7d3463d20b13?auto=format&fit=crop&w=900&q=85",
     "story": "Bright, sunlit slices for the mornings that need a lift and the afternoons that need a smile."},
    {"id": "coconut-loaf", "name": "Coconut Loaf", "price": 1200,
     "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Something different", "Fresh & citrusy"], "occasions": ["Tea party", "Gift", "Eid", "Anniversary"],
     "image": "https://images.unsplash.com/photo-1568051243851-f9b136146e97?auto=format&fit=crop&w=900&q=85",
     "story": "Toasted coconut, soft crumb, quiet luxury — the loaf that surprises everyone at the table."},
    {"id": "coffee-walnut-loaf", "name": "Coffee Loaf with Walnut Crumble", "price": 1350,
     "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Coffee lover", "Warm & comforting"], "occasions": ["Anniversary", "Family gathering", "Graduation", "Tea party"],
     "image": "https://images.unsplash.com/photo-1571115177098-24ec42ed204d?auto=format&fit=crop&w=900&q=85",
     "story": "For the ones who take their afternoons with a strong cup and a slower conversation."},
    {"id": "double-chocolate", "name": "Double Chocolate Loaf", "price": 1800,
     "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Chocolate lover"], "occasions": ["Birthday", "Gift", "Anniversary", "Graduation"],
     "image": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=900&q=85",
     "story": "Dark, dense and deeply chocolate — the loaf you bring when the room needs to gasp a little."},
    {"id": "chocolate-malt", "name": "Chocolate Malt Loaf", "price": 1850,
     "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Chocolate lover", "Something different"], "occasions": ["Birthday", "Gift", "Graduation", "Anniversary"],
     "image": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=900&q=85",
     "story": "Chocolate with a nostalgic malty backbone — the loaf that tastes like a childhood you'd forgotten."},
]


FESTIVE_BOXES = [
    {"id": "anniversary-box", "name": "Anniversary Box", "tagline": "Slow, warm and a little bit romantic.",
     "items": [{"product_id": "double-chocolate", "qty": 1}, {"product_id": "coffee-walnut-loaf", "qty": 1}],
     "image": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=900&q=85"},
    {"id": "birthday-box", "name": "Birthday Box", "tagline": "The loud, chocolatey kind of joy.",
     "items": [{"product_id": "chocolate-chip-banana", "qty": 1}, {"product_id": "chocolate-malt", "qty": 1}],
     "image": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=900&q=85"},
    {"id": "graduation-box", "name": "Graduation Box", "tagline": "A proud, celebratory afternoon.",
     "items": [{"product_id": "coffee-walnut-loaf", "qty": 1}, {"product_id": "chocolate-malt", "qty": 1}],
     "image": "https://images.unsplash.com/photo-1571115177098-24ec42ed204d?auto=format&fit=crop&w=900&q=85"},
    {"id": "eid-box", "name": "Eid Box", "tagline": "Sweet, generous and made for sharing.",
     "items": [{"product_id": "coconut-loaf", "qty": 1}, {"product_id": "apple-cinnamon", "qty": 1}, {"product_id": "lemon-loaf", "qty": 1}],
     "image": "https://images.unsplash.com/photo-1568051243851-f9b136146e97?auto=format&fit=crop&w=900&q=85"},
    {"id": "baby-born-box", "name": "Baby Born Box", "tagline": "Gentle, bright and full of good wishes.",
     "items": [{"product_id": "lemon-loaf", "qty": 1}, {"product_id": "apple-cinnamon", "qty": 1}],
     "image": "https://images.unsplash.com/photo-1519915028121-7d3463d20b13?auto=format&fit=crop&w=900&q=85"},
]


def _by_id():
    return {p["id"]: p for p in PRODUCTS}


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


def _score(product, req: MatchRequest):
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
    return score


def _pick_product(req: MatchRequest):
    return max(PRODUCTS, key=lambda p: _score(p, req))


CATALOGUE_FOR_AI = [
    {"name": p["name"], "price": p["price"], "serves": p["serves"], "moods": p["moods"], "occasions": p["occasions"]}
    for p in PRODUCTS
]


async def ask_baker(prompt: str, session_id: str, system_extra: str = ""):
    key = os.environ["EMERGENT_LLM_KEY"]
    system_message = (
        "You are the warm, concise home baker for Treats & Temptation by SK. "
        "You only bake loaves right now. Only ever mention items from this catalogue: "
        + json.dumps(CATALOGUE_FOR_AI) + ". "
        "Never invent products, prices or ingredients that are not listed. "
        "Speak like a friend, not a menu. Keep replies under 80 words."
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


@api_router.get("/")
async def root():
    return {"message": "Treats & Temptation by SK API"}


@api_router.get("/products")
async def products():
    return PRODUCTS


@api_router.get("/festive-boxes")
async def festive_boxes():
    return [_hydrate_box(b) for b in FESTIVE_BOXES]


@api_router.post("/match")
async def match_dessert(request: MatchRequest):
    best = _pick_product(request)
    prompt = (
        f"The perfect loaf for this customer is: {best['name']} (Rs. {best['price']}, serves {best['serves']}). "
        f"They are buying for a {request.occasion.lower()}, in the mood for {request.mood.lower()}, "
        f"for {request.people} people, budget around Rs. {request.budget}, dietary: {request.dietary}. "
        f"Write ONE warm, personal sentence (max 30 words) explaining why {best['name']} suits them. "
        f"You MUST use the exact name '{best['name']}' and MUST NOT mention any other loaf."
    )
    try:
        explanation = await ask_baker(
            prompt,
            "match-" + uuid.uuid4().hex,
            system_extra=f"For this reply you must only talk about '{best['name']}'."
        )
    except Exception as e:
        logging.getLogger(__name__).warning("match LLM error: %s", e)
        explanation = f"{best['name']} feels just right — warm, homemade, and made for the moment you're planning."
    other_names = [p["name"] for p in PRODUCTS if p["id"] != best["id"]]
    if best["name"].lower() not in explanation.lower() or any(n.lower() in explanation.lower() for n in other_names):
        explanation = f"{best['name']} — a warm, homemade pick for your {request.occasion.lower()}. Perfect for {request.people} and stays gently within your Rs. {request.budget} budget."
    return {"product": best, "explanation": explanation}


@api_router.post("/match/save")
async def save_match(payload: SaveMatchRequest):
    pmap = _by_id()
    if payload.product_id not in pmap:
        raise HTTPException(status_code=404, detail="Unknown product")
    match_id = uuid.uuid4().hex[:10]
    doc = {
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
    await db.saved_matches.insert_one(doc)
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
        reply = await ask_baker(request.message, session_id)
        ok = True
    except Exception as e:
        logging.getLogger(__name__).warning("chat LLM error: %s", e)
        reply = "The oven's a little warm right now — try me again in a moment."
        ok = False
    await db.baker_chats.insert_one({
        "session_id": session_id,
        "message": request.message,
        "reply": reply,
        "ok": ok,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"session_id": session_id, "reply": reply, "ok": ok}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.model_dump())
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks


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
