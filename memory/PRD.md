# Treats & Temptation by SK — PRD

## Problem Statement
Build an AI-powered dessert discovery site (not a plain bakery menu) for a home-bakery brand ("Treats & Temptation by SK"). Users answer occasion/mood/people/budget/dietary questions and receive an AI-personalised bake recommendation, can build a mix-and-match box, chat with an AI baker, and hand off orders via WhatsApp.

## User Personas
- **Gift-buyer**: Doesn't know what to order for a friend's birthday/anniversary — needs guided help.
- **Tea-party host**: Wants a warm, homemade spread within a budget.
- **Craving customer**: Just wants "something sweet" — uses "Surprise Me" or AI Baker Chat.

## Core Requirements (Static)
1. Dessert Matchmaker — form → AI recommendation (product + one warm sentence).
2. Build Your Box — pre-set mix (1 loaf, 2 cookies, 2 brownies, 1 cinnamon roll) with live pricing.
3. Surprise Me — random pick from live catalogue.
4. Story Behind the Bake — each bake has a short story, not a menu blurb.
5. AI Baker Chat — chatbot bounded to the real catalogue.
6. WhatsApp order handoff — cart formatted into wa.me share link.

## Implemented (2026-02)
- FastAPI backend with `/api/products`, `/api/festive-boxes`, `/api/match`, `/api/match/save`, `/api/match/{id}`, `/api/chat`, plus status endpoints.
- **7-loaf catalogue matching SK's real Instagram menu** (Chocolate Chip Banana Bread with walnut add-on, Apple Cinnamon, Lemon, Coconut, Coffee Walnut Crumble, Double Chocolate, Chocolate Malt) with mood/occasion/price metadata.
- Deterministic scoring in `/api/match` (mood + occasion + budget + serves fit) → LLM prose bound to the chosen product name, with safety-net fallback if the model drifts.
- `/api/chat` grounded to catalogue via system prompt; failures return a friendly reply with `ok=false`.
- **Festive Boxes**: 5 curated boxes (Anniversary, Birthday, Graduation, Eid, Baby Born) each with items and a computed total.
- **Save & Share**: `/api/match/save` returns a short id → sharable `?match=<id>` URL; on load the frontend restores the match automatically.
- React frontend: hero, matchmaker form, match result card with Save & Share, festive-boxes section, loaf-mix box builder, stories section, footer.
- Full cart drawer: add-from-match, add-festive-box, add-builder, quantity +/-, remove, running total, "Order via WhatsApp", clear box.
- Cart count badge in navbar (`data-testid=cart-count`).
- AI Baker Chat drawer with loading indicator and visible error banner when backend is down.
- **Real WhatsApp handoff to +92 322 4112832** on every WhatsApp button.
- Emergent LLM Key integration (openai gpt-4o-mini).

## Tech Stack
- Frontend: React (CRA), Tailwind (not used yet — plain CSS in App.css), axios, lucide-react.
- Backend: FastAPI, motor (Mongo), emergentintegrations.
- LLM: Emergent LLM Key.

## Prioritised Backlog
### P1
- Wire up a real WhatsApp business number instead of open `wa.me/` share.
- Real product photography (Instagram scrape was blocked; using Unsplash placeholders).
- Persist chat sessions across drawer reopen; show session history.
- "Save my match" — email/share the recommendation.

### P2
- Order form fallback (name + address) for users without WhatsApp.
- Admin CRUD for products (currently hard-coded).
- Testimonials / social proof section.
- Delivery pincode checker.

## Deferred / Not Requested
- Auth / user accounts.
- Payments (order handoff is via WhatsApp).
- Instagram auto-sync (blocked upstream).

## Known Notes for Next Agent
- Product data is hard-coded in `/app/backend/server.py` (`PRODUCTS`). Frontend fetches them via `/api/products`.
- Match endpoint injects the chosen product name and a strict "must use this exact name" instruction, plus a post-check that rewrites the explanation if the LLM drifts.
- No authentication; all endpoints are public.
