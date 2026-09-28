# Treats & Temptation by SK — PRD

## Problem Statement
AI-powered dessert discovery + custom bake ordering site for home-baker **Sana Khan** (Instagram: @treatsandtemptationbysk). Pakistan-based (WhatsApp +92 322 4112832, PKR). Not a plain menu — customers explore a full menu, get an AI-matched loaf, or build a custom box with ribbon and personalized message, then order on the site.

## User Personas
- **Gift buyer** — no idea what to order for a birthday/anniversary/Eid; needs guided help.
- **Tea-party host** — wants a warm homemade spread within budget.
- **Craving customer** — wants "something sweet"; uses Surprise Me or AI Baker Chat.
- **Occasion sender** — wants a curated small box with ribbon and a personal note for a friend.

## Core Requirements (Static)
1. Dessert Matchmaker — form → AI loaf recommendation (product + one warm sentence).
2. Full Menu at `/menu` — filterable across loaves, cheesecakes, batches, cookies.
3. Custom Box Builder at `/build` — flying-item animation, ribbon options, personalized note.
4. Festive Boxes — 5 one-tap curated pairings.
5. Save & Share match — sharable `?match=<id>` URL.
6. AI Baker Chat — bounded to the real catalogue.
7. On-site checkout at `/checkout` with real order persistence.
8. WhatsApp order handoff for confirmation & bank-transfer payment details.

## Implemented (2026-02)
- **19-item catalogue** matching Sana Khan's real Instagram menu:
  - **Loaves (6)**: Lemon 850, Chocolate Chip Banana 900 (+walnut 100), Apple Cinnamon 850, Coffee Walnut Crumble 1200, Coconut 1200, Sugar-Free Dates 1800.
  - **Cheesecake & Desserts (5)**: NYC 2200, Lotus 2500, Pineapple 1800, Banoffee Pie 2100, Coffee Cake w/ Nutty Brittle 1200.
  - **Batches (4)**: Brownies 1000/4, Cinnamon Rolls 1400/4, Papparoti Buns 800/4, Éclair 700/3.
  - **Cookies (4, per piece)**: Chocolate Chip 200, Chocolate Filled 250, Lotus 300, Double Chocolate 300.
- **Custom-box unit pricing** for small mixes: brownie 275, cinnamon roll 375, papparoti 225, éclair 250, cookies at piece price.
- **Packaging**: Plain White (Rs 100), White Ribbon (Rs 150), Pink Ribbon (Rs 150).
- **Pages/routes** via react-router: `/`, `/menu`, `/build`, `/festive/:boxId`, `/checkout`, `/order/:orderNumber`.
- **Custom Box Builder** (`/build`) with flying-image animation; ribbon renders when selected; personalized message shows as a hanging tag; per-piece pricing.
- **Festive Box Editor** (`/festive/:boxId`) — start from a curated pairing (Anniversary/Birthday/Graduation/Eid/Baby Born), add/remove/swap items via a full-catalogue picker, adjust qty, swap ribbon, add note; uses each product's full/batch price on checkout.
- **Home festive cards** show pink gift-box imagery + a "Customize" button that opens the editor.
- **Checkout** with form validation, delivery date, notes, packaging cache fallback (no flicker).
- **Orders persisted** in MongoDB (`db.orders`) with unique `TT######` order number.
- **Order success page** with formatted WhatsApp handoff pre-filled with every line item + packaging + note + customer info; SK confirms & shares bank details.
- **Save & Share match** — `?match=<id>` URL, copy-to-clipboard.
- **AI Baker Chat** grounded to the full 19-item catalogue.
- **Pink & white theme** matching Sana Khan's brand identity; **logo** displayed as circular stamp on hero image.
- **Cart** persists in localStorage across routes.
- Emergent LLM Key (openai gpt-4o-mini).

## Tech Stack
- Frontend: React + react-router-dom, plain CSS in App.css.
- Backend: FastAPI, motor (Mongo), emergentintegrations.
- LLM: Emergent LLM Key.
- Payment: Bank transfer via WhatsApp (Stripe unavailable in PK).

## Deferred / Not Requested
- Online card payments — Stripe sandbox is `country_not_supported` for PK. User picked bank-transfer via WhatsApp instead.
- Auth / user accounts.
- Admin CRUD for products (currently hard-coded).
- Instagram auto-sync (upstream blocked).

## Prioritized Backlog
### P1
- Real product photography (currently high-quality Unsplash placeholders).
- Admin product editor page (auth-protected).
- Order status timeline (pending → confirmed → out for delivery → delivered) with WhatsApp status pushes.
- SMS/email notifications on order confirm.

### P2
- Delivery pincode / zone checker.
- Testimonials / social proof section.
- Loyalty coupon codes.
- Voice-driven Baker Chat (whisper).

## Known Notes for Next Agent
- All product data hard-coded in `/app/backend/server.py` under `PRODUCTS`; add `custom_box_unit` on a product to make it available in the Build-a-Box picker.
- Cart uses composite key `${id}::cbox` vs plain `id` — same product can appear twice with different modes.
- Stripe is intentionally not integrated; if user opens a PayPro/SafePay merchant account, playbook the integration then.
- Logo image is a screenshot with Instagram UI chrome; hero uses a tightly-cropped CSS background-image to isolate just the badge. When SK sends a clean logo, swap the URL and remove the `background-size / background-position` fine-tuning in `.logo-stamp`.
