import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ArrowRight, ChevronLeft, ChevronRight, Instagram, Link2, MessageCircle, Minus, Plus, ShoppingBag, Sparkles, WandSparkles } from "lucide-react";
import { api } from "@/state/api";
import { useCart } from "@/state/CartContext";

const occasions = [
  "Birthday", "Anniversary", "Tea party", "Family gathering",
  "Graduation", "Eid", "Baby born", "Gift", "Just craving something",
];
const moods = ["Chocolate lover", "Fresh & citrusy", "Warm & comforting", "Coffee lover", "Something different"];

const HERO_SLIDES = [
  {
    image: "https://res.cloudinary.com/dffsqfwok/image/upload/v1790758951/Commercial_bakery_products_on_ta__2K_20260930140220_ggjrdi.jpg",
    alt: "Homemade artisanal bakes and loaves",
  },
  {
    image: "https://res.cloudinary.com/dffsqfwok/image/upload/w_900,q_auto,f_auto/v1790760596/Mango_dessert_trays_on_surface_2K_20260930142859_zpcb6w.jpg",
    alt: "Signature mango dessert trays and cups",
  },
  {
    image: "https://res.cloudinary.com/dffsqfwok/image/upload/v1790778866/WhatsApp_Image_2026-09-30_at_14.22.37.jpeg_2K_20260930193407_k7nfcn.jpg",
    alt: "Curated festive dessert boxes",
  },
  {
    image: "https://images.unsplash.com/photo-1621994214182-f467e6999dc9?auto=format&fit=crop&w=900&q=85",
    alt: "Chocolate chip banana bread",
  },
  {
    image: "https://images.unsplash.com/photo-1509365465985-25d11c17e812?auto=format&fit=crop&w=900&q=85",
    alt: "Freshly glazed cinnamon rolls",
  },
];

function slug(x) { return x.toLowerCase().replaceAll(" ", "-").replaceAll("&", "and"); }

export default function Home() {
  const [products, setProducts] = useState([]);
  const [loaves, setLoaves] = useState([]);
  const [boxes, setBoxes] = useState([]);
  const [occasion, setOccasion] = useState("Tea party");
  const [mood, setMood] = useState("Warm & comforting");
  const [people, setPeople] = useState(6);
  const [budget, setBudget] = useState(1500);
  const [dietary, setDietary] = useState("No preference");
  const [match, setMatch] = useState(null);
  const [matchError, setMatchError] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedNote, setSavedNote] = useState("");
  const [heroSlide, setHeroSlide] = useState(0);
  const [isHeroPaused, setIsHeroPaused] = useState(false);
  const location = useLocation();
  const { addItem, setCartOpen } = useCart();

  useEffect(() => {
    if (isHeroPaused) return;
    const interval = setInterval(() => {
      setHeroSlide((prev) => (prev + 1) % HERO_SLIDES.length);
    }, 4500);
    return () => clearInterval(interval);
  }, [isHeroPaused]);

  const prevSlide = () => setHeroSlide((prev) => (prev - 1 + HERO_SLIDES.length) % HERO_SLIDES.length);
  const nextSlide = () => setHeroSlide((prev) => (prev + 1) % HERO_SLIDES.length);

  useEffect(() => {
    api.get("/products").then((r) => {
      setProducts(r.data);
      setLoaves(r.data.filter((p) => p.category === "loaf"));
    }).catch(() => {});
    api.get("/festive-boxes").then((r) => setBoxes(r.data)).catch(() => {});
    const params = new URLSearchParams(window.location.search);
    const savedId = params.get("match");
    if (savedId) {
      api.get(`/match/${savedId}`).then((r) => {
        setMatch({ product: r.data.product, explanation: r.data.explanation });
        setTimeout(() => document.getElementById("match-result")?.scrollIntoView({ behavior: "smooth" }), 300);
      }).catch(() => {});
    }
  }, []);

  useEffect(() => {
    if (location.hash) {
      const el = document.querySelector(location.hash);
      if (el) setTimeout(() => el.scrollIntoView({ behavior: "smooth" }), 80);
    }
  }, [location]);

  const runMatch = async () => {
    setLoading(true); setMatchError(""); setSavedNote("");
    try {
      const r = await api.post("/match", { occasion, mood, people, budget: Number(budget) || 0, dietary });
      setMatch(r.data);
      setTimeout(() => document.getElementById("match-result")?.scrollIntoView({ behavior: "smooth" }), 60);
    } catch {
      setMatchError("Our little kitchen is offline for a moment — please try again shortly.");
    } finally { setLoading(false); }
  };

  const surprise = () => {
    if (!loaves.length) return;
    const picked = loaves[Math.floor(Math.random() * loaves.length)];
    setMatch({ product: picked, explanation: `${picked.name} — a little baker's instinct says this is the loaf you didn't know you were craving.` });
    setSavedNote("");
    setTimeout(() => document.getElementById("match-result")?.scrollIntoView({ behavior: "smooth" }), 60);
  };

  const saveMatch = async () => {
    if (!match || saving) return;
    setSaving(true); setSavedNote("");
    try {
      const r = await api.post("/match/save", {
        product_id: match.product.id, occasion, mood, people,
        budget: Number(budget) || 0, dietary, explanation: match.explanation,
      });
      const url = `${window.location.origin}/?match=${r.data.id}`;
      try {
        await navigator.clipboard.writeText(url);
        setSavedNote("Link copied — paste it anywhere to come back to this bake.");
      } catch { setSavedNote(url); }
    } catch { setSavedNote("Couldn't save right now — please try again in a moment."); }
    finally { setSaving(false); }
  };

  const addMatchToCart = () => {
    if (!match) return;
    addItem({ id: match.product.id, name: match.product.name, price: match.product.price, image: match.product.image, custom_box: false });
    setCartOpen(true);
  };

  const addFestive = (box) => {
    box.items.forEach(({ product, qty }) => {
      addItem({ id: product.id, name: product.name, price: product.price, image: product.image, custom_box: false, qty });
    });
    setCartOpen(true);
  };

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">HOMEMADE, MATCHED TO THE MOMENT</p>
          <h1>Find the bake<br /><em>you feel like.</em></h1>
          <p className="hero-text">
            Not sure what to order? Tell us the occasion, the mood and who's coming. We'll match you with the bake that fits — or build your own box, your way.
          </p>
          <div className="hero-actions">
            <a href="#match" className="button primary" data-testid="hero-find-bake">
              Find my perfect bake <ArrowRight size={17} />
            </a>
            <Link to="/build" className="button text-button" data-testid="hero-build-box">
              <WandSparkles size={17} /> Build a box
            </Link>
          </div>
          <div className="hero-note">
            <Sparkles size={16} /> Baked in small batches, chosen with care
          </div>
        </div>
        <div
          className="hero-image"
          onMouseEnter={() => setIsHeroPaused(true)}
          onMouseLeave={() => setIsHeroPaused(false)}
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "ArrowLeft") prevSlide();
            if (e.key === "ArrowRight") nextSlide();
          }}
          aria-label="Bakery showcase slideshow"
        >
          <div className="hero-slides-wrapper">
            {HERO_SLIDES.map((slide, idx) => (
              <div
                key={idx}
                className={`hero-slide ${idx === heroSlide ? "active" : ""}`}
                aria-hidden={idx !== heroSlide}
              >
                <img
                  src={slide.image}
                  alt={slide.alt}
                  loading={idx === 0 ? "eager" : "lazy"}
                  data-testid={idx === 0 ? "hero-dessert-image" : undefined}
                />
              </div>
            ))}
          </div>

          <button
            type="button"
            className="hero-slider-arrow prev"
            onClick={prevSlide}
            aria-label="Previous slide"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            type="button"
            className="hero-slider-arrow next"
            onClick={nextSlide}
            aria-label="Next slide"
          >
            <ChevronRight size={18} />
          </button>

          <div className="hero-slider-dots">
            {HERO_SLIDES.map((_, idx) => (
              <button
                type="button"
                key={idx}
                className={`hero-dot ${idx === heroSlide ? "active" : ""}`}
                onClick={() => setHeroSlide(idx)}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>

          <div className="image-stamp logo-stamp">
          </div>
        </div>
      </section>

      <section className="match-section" id="match">
        <div className="section-intro">
          <p className="eyebrow">01 / THE LOAF MATCHMAKER</p>
          <h2>Let's find your<br /><em>perfect match.</em></h2>
          <p>A few little questions, then a loaf recommendation that feels like it was made for you.</p>
          <button className="button text-button" style={{ marginTop: 22 }} onClick={surprise} data-testid="hero-surprise-button">
            <WandSparkles size={17} /> Surprise me
          </button>
        </div>
        <div className="match-form">
          <div className="question">
            <label>Who are you buying for?</label>
            <div className="choice-grid">
              {occasions.map((x) => (
                <button className={occasion === x ? "choice active" : "choice"} onClick={() => setOccasion(x)} data-testid={`occasion-${slug(x)}`} key={x}>{x}</button>
              ))}
            </div>
          </div>
          <div className="question">
            <label>What's your mood?</label>
            <div className="choice-grid">
              {moods.map((x) => (
                <button className={mood === x ? "choice active" : "choice"} onClick={() => setMood(x)} data-testid={`mood-${slug(x)}`} key={x}>{x}</button>
              ))}
            </div>
          </div>
          <div className="split-questions">
            <div className="question">
              <label>How many people?</label>
              <div className="stepper">
                <button onClick={() => setPeople(Math.max(1, people - 1))} data-testid="people-minus"><Minus size={15} /></button>
                <strong data-testid="people-count">{people}</strong>
                <button onClick={() => setPeople(people + 1)} data-testid="people-plus"><Plus size={15} /></button>
              </div>
            </div>
            <div className="question">
              <label>Budget</label>
              <div className="budget-input">
                <span>Rs.</span>
                <input value={budget} onChange={(e) => setBudget(e.target.value)} data-testid="budget-input" />
              </div>
            </div>
          </div>
          <div className="question">
            <label>Any dietary preferences?</label>
            <select value={dietary} onChange={(e) => setDietary(e.target.value)} data-testid="dietary-select">
              <option>No preference</option>
              <option>Eggless</option>
              <option>Less sweet</option>
              <option>Sugar-free</option>
              <option>Gluten conscious</option>
            </select>
          </div>
          {matchError && <p className="inline-error" data-testid="match-error">{matchError}</p>}
          <button className="button primary wide" onClick={runMatch} disabled={loading} data-testid="find-match-button">
            {loading ? "Finding your match…" : <>Find my perfect match <ArrowRight size={17} /></>}
          </button>
        </div>
      </section>

      {match && (
        <section className="result-section" id="match-result">
          <div className="result-card">
            <div className="result-image">
              <img src={match.product.image} alt={match.product.name} data-testid="match-product-image" />
              <span>YOUR PERFECT MATCH</span>
            </div>
            <div className="result-copy">
              <p className="eyebrow">A NOTE FROM THE BAKER</p>
              <h2 data-testid="match-product-name">{match.product.name}</h2>
              <p className="result-description" data-testid="match-explanation">{match.explanation}</p>
              <p className="story">"{match.product.story}"</p>
              {match.product.addons?.length > 0 && (
                <p className="addon-note" data-testid="match-addons">
                  Add-on: {match.product.addons.map((a) => `${a.name} (+Rs. ${a.price})`).join(", ")}
                </p>
              )}
              <div className="result-meta">
                <span>Serves {match.product.serves}</span>
                <b>Rs. {match.product.price.toLocaleString()}</b>
              </div>
              <div className="result-actions">
                <button className="button primary" onClick={addMatchToCart} data-testid="add-match-to-cart">
                  Add to my box <ShoppingBag size={17} />
                </button>
                <button className="button ghost" onClick={saveMatch} disabled={saving} data-testid="save-match-button">
                  {saving ? "Saving…" : <>Save & share <Link2 size={16} /></>}
                </button>
              </div>
              {savedNote && <p className="saved-note" data-testid="saved-note">{savedNote}</p>}
            </div>
          </div>
        </section>
      )}

      <section className="festive-section" id="festive">
        <div className="festive-heading">
          <p className="eyebrow">02 / READY-MADE FESTIVE BOXES</p>
          <h2>One-tap<br /><em>gifting.</em></h2>
          <p>Curated pairings for the moments you don't want to think twice about.</p>
        </div>
        <div className="festive-grid">
          {boxes.map((box) => (
            <article className="festive-card" key={box.id} data-testid={`festive-${box.id}`}>
              <div className="festive-image">
                <img src={box.image} alt={box.name} loading="lazy" referrerPolicy="no-referrer" />
              </div>
              <div className="festive-body">
                <h3>{box.name}</h3>
                <p className="festive-tagline">{box.tagline}</p>
                <ul className="festive-items">
                  {box.items.map(({ product, qty }) => (<li key={product.id}>{qty}× {product.name}</li>))}
                </ul>
                <div className="festive-footer">
                  <b>from Rs. {box.total.toLocaleString()}</b>
                  <div className="festive-actions">
                    <Link className="button primary small" to={`/festive/${box.id}`} data-testid={`festive-customize-${box.id}`}>
                      Customize <ArrowRight size={14} />
                    </Link>
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="build-cta">
        <div>
          <p className="eyebrow">03 / OR MAKE IT YOURS</p>
          <h2>Build a box, your way.</h2>
          <p>Mix small treats — brownies, cookies, cinnamon rolls, éclairs. Pick a ribbon. Add a note.</p>
        </div>
        <Link to="/build" className="button primary" data-testid="cta-build-box">
          Start building <ArrowRight size={17} />
        </Link>
      </section>

      <section className="stories" id="stories">
        <div>
          <p className="eyebrow">04 / STORY BEHIND THE BAKE</p>
          <h2>Good things<br /><em>take time.</em></h2>
          <p className="story-lead">Every loaf has a mood, a memory, a reason to be shared. Here are a few of ours.</p>
          <a className="inline-link" href="https://www.instagram.com/treatsandtemptationbysk/" target="_blank" rel="noreferrer" data-testid="instagram-link">
            See more on Instagram <Instagram size={17} />
          </a>
        </div>
        <div className="story-grid">
          {products.slice(0, 3).map((p) => (
            <article className="tile" key={p.id} tabIndex={0}>
              <div className="image-wrapper">
                <img src={p.image} alt={p.name} loading="lazy" referrerPolicy="no-referrer" />
              </div>

              <div className="story-card">
                <div className="story-eyebrow" title={p.story}>
                  <span>{p.name.toUpperCase()}</span>
                  <span className="star">✦</span>
                </div>

                <div className="story-copy">
                  “{p.story}”
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
