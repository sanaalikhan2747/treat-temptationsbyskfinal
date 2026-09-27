from fastapi import FastAPI, APIRouter
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

# MongoDB connection
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


PRODUCTS = [
    {"id": "chocolate-cake", "name": "Chocolate Celebration Cake", "price": 1200, "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Chocolate lover"], "occasions": ["Birthday", "Gift", "Anniversary"],
     "image": "https://images.unsplash.com/photo-1700448293876-07dca826c161?auto=format&fit=crop&w=900&q=85",
     "story": "The cake you bring when the room deserves a little more chocolate."},
    {"id": "cinnamon-rolls", "name": "Cinnamon Rolls", "price": 650, "serves_min": 4, "serves_max": 6, "serves": "4–6",
     "moods": ["Warm & comforting"], "occasions": ["Tea party", "Family gathering"],
     "image": "https://images.unsplash.com/photo-1694632288834-17d86b340745?auto=format&fit=crop&w=900&q=85",
     "story": "The box that makes an ordinary afternoon smell like a Sunday morning."},
    {"id": "banana-loaf", "name": "Chocolate Chip Banana Loaf", "price": 750, "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Warm & comforting", "Something different"], "occasions": ["Tea party", "Just craving something"],
     "image": "https://images.unsplash.com/photo-1621994214182-f467e6999dc9?auto=format&fit=crop&w=900&q=85",
     "story": "A tender little loaf for slow tea, second slices and a warm kitchen."},
    {"id": "brownies", "name": "Fudge Brownie Box", "price": 550, "serves_min": 4, "serves_max": 6, "serves": "4–6",
     "moods": ["Chocolate lover"], "occasions": ["Gift", "Just craving something"],
     "image": "https://images.unsplash.com/photo-1642453031286-8991becafe19?auto=format&fit=crop&w=900&q=85",
     "story": "Dense, fudgy and gone before you remember to save one for later."},
    {"id": "lemon-loaf", "name": "Lemon Drizzle Loaf", "price": 700, "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Fresh & citrusy"], "occasions": ["Tea party", "Gift", "Just craving something"],
     "image": "https://images.unsplash.com/photo-1519915028121-7d3463d20b13?auto=format&fit=crop&w=900&q=85",
     "story": "A bright, sunlit slice for the mornings that need a little lift."},
    {"id": "coffee-walnut", "name": "Coffee & Walnut Cake", "price": 950, "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Coffee lover"], "occasions": ["Anniversary", "Family gathering", "Tea party"],
     "image": "https://images.unsplash.com/photo-1571115177098-24ec42ed204d?auto=format&fit=crop&w=900&q=85",
     "story": "For the ones who take their afternoons with a cup of something strong."},
    {"id": "cookie-jar", "name": "Assorted Cookie Jar", "price": 500, "serves_min": 4, "serves_max": 6, "serves": "4–6",
     "moods": ["Chocolate lover", "Something different"], "occasions": ["Gift", "Just craving something"],
     "image": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&w=900&q=85",
     "story": "A jar you keep on the counter and pretend you didn't finish in a week."},
    {"id": "cheesecake", "name": "Baked New York Cheesecake", "price": 1100, "serves_min": 6, "serves_max": 8, "serves": "6–8",
     "moods": ["Fresh & citrusy", "Something different"], "occasions": ["Anniversary", "Birthday", "Gift"],
     "image": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=900&q=85",
     "story": "Slow-baked, gently vanilla and quietly show-stopping."},
]


def _score(product, req: MatchRequest):
    score = 0
    if req.mood in product["moods"]:
        score += 3
    if req.occasion in product["occasions"]:
        score += 3
    if product["price"] <= req.budget:
        score += 2
    # closer serving size wins ties
    mid = (product["serves_min"] + product["serves_max"]) / 2
    score -= abs(mid - req.people) * 0.1
    # small penalty if very over budget
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
        "Only ever mention items from this catalogue: " + json.dumps(CATALOGUE_FOR_AI) + ". "
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


@api_router.post("/match")
async def match_dessert(request: MatchRequest):
    best = _pick_product(request)
    prompt = (
        f"The perfect bake for this customer is: {best['name']} (Rs. {best['price']}, serves {best['serves']}). "
        f"They are buying for a {request.occasion.lower()}, in the mood for {request.mood.lower()}, "
        f"for {request.people} people, budget around Rs. {request.budget}, dietary: {request.dietary}. "
        f"Write ONE warm, personal sentence (max 30 words) explaining why {best['name']} suits them. "
        f"You MUST use the exact name '{best['name']}' and MUST NOT mention any other bake."
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
    # Safety net: if LLM still drifted and named a different product, prepend the correct name.
    other_names = [p["name"] for p in PRODUCTS if p["id"] != best["id"]]
    if best["name"].lower() not in explanation.lower() or any(n.lower() in explanation.lower() for n in other_names):
        explanation = f"{best['name']} — a warm, homemade pick for your {request.occasion.lower()}. Perfect for {request.people} and stays gently within your Rs. {request.budget} budget."
    return {"product": best, "explanation": explanation}


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
