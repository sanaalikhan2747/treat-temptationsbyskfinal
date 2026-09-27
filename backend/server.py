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

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
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

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Treats & Temptation by SK API"}

PRODUCTS = [
    {"id": "chocolate-cake", "name": "Chocolate Celebration Cake", "price": 1200, "serves": "6–8", "moods": ["Chocolate lover"], "occasions": ["Birthday", "Gift"], "image": "https://images.unsplash.com/photo-1700448293876-07dca826c161?auto=format&fit=crop&w=900&q=85", "story": "The cake you bring when the room deserves a little more chocolate."},
    {"id": "cinnamon-rolls", "name": "Cinnamon Rolls", "price": 650, "serves": "4–6", "moods": ["Warm & comforting"], "occasions": ["Tea party", "Family gathering"], "image": "https://images.unsplash.com/photo-1694632288834-17d86b340745?auto=format&fit=crop&w=900&q=85", "story": "The box that makes an ordinary afternoon smell like a Sunday morning."},
    {"id": "banana-loaf", "name": "Chocolate Chip Banana Loaf", "price": 750, "serves": "6–8", "moods": ["Warm & comforting", "Something different"], "occasions": ["Tea party", "Just craving something"], "image": "https://images.unsplash.com/photo-1621994214182-f467e6999dc9?auto=format&fit=crop&w=900&q=85", "story": "A tender little loaf for slow tea, second slices and a warm kitchen."},
    {"id": "brownies", "name": "Fudge Brownie Box", "price": 550, "serves": "4–6", "moods": ["Chocolate lover"], "occasions": ["Gift", "Just craving something"], "image": "https://images.unsplash.com/photo-1642453031286-8991becafe19?auto=format&fit=crop&w=900&q=85", "story": "Dense, fudgy and gone before you remember to save one for later."}
]

async def ask_baker(prompt: str, session_id: str):
    key = os.environ["EMERGENT_LLM_KEY"]
    chat = LlmChat(api_key=key, session_id=session_id, system_message="You are the warm, concise baker for Treats & Temptation by SK. Only recommend from this catalogue: " + json.dumps(PRODUCTS) + ". Never invent products or prices. Mention the relevant product name and price. Keep replies under 90 words.").with_model("openai", "gpt-5.4")
    text = ""
    async for event in chat.stream_message(UserMessage(text=prompt)):
        if isinstance(event, TextDelta):
            text += event.content
        elif isinstance(event, StreamDone):
            break
    return text

@api_router.post("/match")
async def match_dessert(request: MatchRequest):
    matches = [p for p in PRODUCTS if (request.mood in p["moods"] or request.occasion in p["occasions"]) and p["price"] <= request.budget]
    if not matches:
        matches = [p for p in PRODUCTS if p["price"] <= request.budget] or PRODUCTS
    best = matches[0]
    prompt = f"Recommend one perfect match for occasion={request.occasion}, mood={request.mood}, people={request.people}, budget={request.budget}, dietary={request.dietary}. Start with the exact product name, then give one warm sentence."
    explanation = await ask_baker(prompt, "match-" + uuid.uuid4().hex)
    return {"product": best, "explanation": explanation}

@api_router.post("/chat")
async def baker_chat(request: ChatRequest):
    session_id = request.session_id or "chat-" + uuid.uuid4().hex
    reply = await ask_baker(request.message, session_id)
    await db.baker_chats.insert_one({"session_id": session_id, "message": request.message, "reply": reply, "created_at": datetime.now(timezone.utc).isoformat()})
    return {"session_id": session_id, "reply": reply}

@api_router.get("/products")
async def products():
    return PRODUCTS

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()