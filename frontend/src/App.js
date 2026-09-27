import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { ArrowRight, Copy, Instagram, Link2, MessageCircle, Minus, Plus, ShoppingBag, Sparkles, Trash2, WandSparkles, X } from "lucide-react";
import "@/App.css";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const WHATSAPP_PHONE = "923224112832"; // +92 322 4112832

const occasions = [
  "Birthday",
  "Anniversary",
  "Tea party",
  "Family gathering",
  "Graduation",
  "Eid",
  "Baby born",
  "Gift",
  "Just craving something",
];
const moods = ["Chocolate lover", "Fresh & citrusy", "Warm & comforting", "Coffee lover", "Something different"];

const DEFAULT_BOX = [
  { id: "chocolate-chip-banana", qty: 1 },
  { id: "apple-cinnamon", qty: 1 },
  { id: "lemon-loaf", qty: 1 },
];

function slug(x) {
  return x.toLowerCase().replaceAll(" ", "-").replaceAll("&", "and");
}

function waLink(text) {
  return `https://wa.me/${WHATSAPP_PHONE}?text=${encodeURIComponent(text)}`;
}

function App() {
  const [products, setProducts] = useState([]);
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
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [builderQtys, setBuilderQtys] = useState({});
  const [chatOpen, setChatOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [chatError, setChatError] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chat, setChat] = useState([
    { role: "assistant", text: "Tell me who you're baking for, and I'll pick the loaf that fits the moment." },
  ]);

  useEffect(() => {
    axios.get(`${API}/products`).then((r) => {
      setProducts(r.data);
      const seed = Object.fromEntries(r.data.map((p) => [p.id, 0]));
      DEFAULT_BOX.forEach(({ id, qty }) => { if (seed[id] !== undefined) seed[id] = qty; });
      setBuilderQtys(seed);
    }).catch(() => setProducts([]));
    axios.get(`${API}/festive-boxes`).then((r) => setBoxes(r.data)).catch(() => setBoxes([]));

    const params = new URLSearchParams(window.location.search);
    const savedId = params.get("match");
    if (savedId) {
      axios.get(`${API}/match/${savedId}`).then((r) => {
        setMatch({ product: r.data.product, explanation: r.data.explanation });
        setTimeout(() => document.getElementById("match-result")?.scrollIntoView({ behavior: "smooth" }), 300);
      }).catch(() => {});
    }
  }, []);

  const productById = useMemo(() => Object.fromEntries(products.map((p) => [p.id, p])), [products]);
  const cartCount = useMemo(() => cart.reduce((n, i) => n + i.qty, 0), [cart]);
  const cartTotal = useMemo(() => cart.reduce((n, i) => n + i.qty * i.price, 0), [cart]);
  const builderItems = useMemo(
    () => products.map((p) => ({ product: p, qty: builderQtys[p.id] || 0 })).filter((r) => r.qty > 0),
    [products, builderQtys]
  );
  const builderTotal = useMemo(
    () => builderItems.reduce((n, r) => n + r.qty * r.product.price, 0),
    [builderItems]
  );

  const bumpBuilder = (id, delta) =>
    setBuilderQtys((q) => ({ ...q, [id]: Math.max(0, (q[id] || 0) + delta) }));

  const addToCart = (product, qty = 1) => {
    setCart((items) => {
      const existing = items.find((i) => i.id === product.id);
      if (existing) return items.map((i) => (i.id === product.id ? { ...i, qty: i.qty + qty } : i));
      return [...items, { id: product.id, name: product.name, price: product.price, image: product.image, qty }];
    });
    setCartOpen(true);
  };
  const addBuilderToCart = () => {
    if (!builderItems.length) return;
    setCart((items) => {
      const next = [...items];
      builderItems.forEach(({ product, qty }) => {
        const existing = next.find((i) => i.id === product.id);
        if (existing) existing.qty += qty;
        else next.push({ id: product.id, name: product.name, price: product.price, image: product.image, qty });
      });
      return next;
    });
    setCartOpen(true);
  };
  const addFestiveBox = (box) => {
    setCart((items) => {
      const next = [...items];
      box.items.forEach(({ product, qty }) => {
        const existing = next.find((i) => i.id === product.id);
        if (existing) existing.qty += qty;
        else next.push({ id: product.id, name: product.name, price: product.price, image: product.image, qty });
      });
      return next;
    });
    setCartOpen(true);
  };
  const updateQty = (id, delta) =>
    setCart((items) => items.map((i) => (i.id === id ? { ...i, qty: Math.max(1, i.qty + delta) } : i)));
  const removeFromCart = (id) => setCart((items) => items.filter((i) => i.id !== id));
  const clearCart = () => setCart([]);

  const runMatch = async () => {
    setLoading(true);
    setMatchError("");
    setSavedNote("");
    try {
      const r = await axios.post(`${API}/match`, { occasion, mood, people, budget: Number(budget) || 0, dietary });
      setMatch(r.data);
      setTimeout(() => document.getElementById("match-result")?.scrollIntoView({ behavior: "smooth" }), 60);
    } catch {
      setMatchError("Our little kitchen is offline for a moment — please try again shortly.");
    } finally {
      setLoading(false);
    }
  };

  const surprise = () => {
    if (!products.length) return;
    const picked = products[Math.floor(Math.random() * products.length)];
    setMatch({
      product: picked,
      explanation: `${picked.name} — a little baker's instinct says this is the loaf you didn't know you were craving.`,
    });
    setSavedNote("");
    setTimeout(() => document.getElementById("match-result")?.scrollIntoView({ behavior: "smooth" }), 60);
  };

  const saveMatch = async () => {
    if (!match || saving) return;
    setSaving(true);
    setSavedNote("");
    try {
      const r = await axios.post(`${API}/match/save`, {
        product_id: match.product.id,
        occasion, mood, people, budget: Number(budget) || 0, dietary,
        explanation: match.explanation,
      });
      const url = `${window.location.origin}${window.location.pathname}?match=${r.data.id}`;
      try {
        await navigator.clipboard.writeText(url);
        setSavedNote("Link copied — paste it anywhere to come back to this bake.");
      } catch {
        setSavedNote(url);
      }
    } catch {
      setSavedNote("Couldn't save right now — please try again in a moment.");
    } finally {
      setSaving(false);
    }
  };

  const sendChat = async () => {
    if (!message.trim() || chatLoading) return;
    const text = message.trim();
    setMessage("");
    setChat((c) => [...c, { role: "user", text }]);
    setChatError("");
    setChatLoading(true);
    try {
      const r = await axios.post(`${API}/chat`, { message: text });
      setChat((c) => [...c, { role: "assistant", text: r.data.reply }]);
      if (r.data.ok === false) setChatError("Live baker unavailable — showing a friendly fallback.");
    } catch {
      setChat((c) => [...c, { role: "assistant", text: "The oven's a little warm right now — try me again in a moment." }]);
      setChatError("Live baker unavailable — try again in a moment.");
    } finally {
      setChatLoading(false);
    }
  };

  const whatsappOrder = () => {
    let text;
    if (cart.length) {
      const lines = cart.map((i) => `• ${i.qty}× ${i.name} — Rs. ${(i.qty * i.price).toLocaleString()}`).join("\n");
      text = `Hello Treats & Temptation by SK!\nI'd like to order:\n${lines}\n\nTotal: Rs. ${cartTotal.toLocaleString()}`;
    } else if (match) {
      text = `Hello Treats & Temptation by SK!\nI'd like to order the ${match.product.name} — Rs. ${match.product.price.toLocaleString()}.`;
    } else {
      text = `Hello Treats & Temptation by SK! I'd like to place an order.`;
    }
    window.open(waLink(text), "_blank");
  };

  const whatsappBox = (box) => {
    const lines = box.items.map(({ product, qty }) => `• ${qty}× ${product.name}`).join("\n");
    const text = `Hello Treats & Temptation by SK!\nI'd like to order the ${box.name}:\n${lines}\n\nTotal: Rs. ${box.total.toLocaleString()}`;
    window.open(waLink(text), "_blank");
  };

  return (
    <div className="site-shell">
      <nav className="nav">
        <a className="brand" href="#top" data-testid="brand-home">
          <span className="brand-mark">SK</span>
          <span>Treats &<br /><b>Temptation</b></span>
        </a>
        <div className="nav-links">
          <a href="#match" data-testid="nav-match">Find your loaf</a>
          <a href="#festive" data-testid="nav-festive">Festive boxes</a>
          <a href="#box" data-testid="nav-box">Build a box</a>
          <a href="#stories" data-testid="nav-stories">Bake stories</a>
        </div>
        <button className="icon-button" onClick={() => setChatOpen(true)} data-testid="open-baker-chat" aria-label="Open baker chat">
          <MessageCircle size={21} />
        </button>
        <button className="cart-pill" onClick={() => setCartOpen(true)} data-testid="cart-button" aria-label="Open cart">
          <ShoppingBag size={18} />
          <span data-testid="cart-count">{cartCount}</span>
        </button>
      </nav>

      <main id="top">
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">HOMEMADE LOAVES, MATCHED TO THE MOMENT</p>
            <h1>Find the loaf<br /><em>you feel like.</em></h1>
            <p className="hero-text">
              Not sure what to order? Tell us the occasion, the mood and who's coming.
              We'll match you with the loaf that fits.
            </p>
            <div className="hero-actions">
              <a href="#match" className="button primary" data-testid="hero-find-bake">
                Find my perfect loaf <ArrowRight size={17} />
              </a>
              <button className="button text-button" onClick={surprise} data-testid="hero-surprise-button">
                <WandSparkles size={17} /> Surprise me
              </button>
            </div>
            <div className="hero-note">
              <Sparkles size={16} /> Baked in small batches, chosen with care
            </div>
          </div>
          <div className="hero-image">
            <img
              src="https://images.unsplash.com/photo-1621994214182-f467e6999dc9?auto=format&fit=crop&w=1300&q=85"
              alt="Homemade loaf on a wooden board"
              data-testid="hero-dessert-image"
            />
            <div className="image-stamp">made for<br /><b>your moment</b></div>
          </div>
        </section>

        <section className="match-section" id="match">
          <div className="section-intro">
            <p className="eyebrow">01 / THE LOAF MATCHMAKER</p>
            <h2>Let's find your<br /><em>perfect match.</em></h2>
            <p>A few little questions, then a recommendation that feels like it was made for you.</p>
          </div>
          <div className="match-form">
            <div className="question">
              <label>Who are you buying for?</label>
              <div className="choice-grid">
                {occasions.map((x) => (
                  <button
                    className={occasion === x ? "choice active" : "choice"}
                    onClick={() => setOccasion(x)}
                    data-testid={`occasion-${slug(x)}`}
                    key={x}
                  >
                    {x}
                  </button>
                ))}
              </div>
            </div>
            <div className="question">
              <label>What's your mood?</label>
              <div className="choice-grid">
                {moods.map((x) => (
                  <button
                    className={mood === x ? "choice active" : "choice"}
                    onClick={() => setMood(x)}
                    data-testid={`mood-${slug(x)}`}
                    key={x}
                  >
                    {x}
                  </button>
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
                  <button className="button primary" onClick={() => addToCart(match.product)} data-testid="add-match-to-cart">
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
            <p>Curated loaf pairings for the moments you don't want to think twice about.</p>
          </div>
          <div className="festive-grid">
            {boxes.map((box) => (
              <article className="festive-card" key={box.id} data-testid={`festive-${box.id}`}>
                <div className="festive-image">
                  <img src={box.image} alt={box.name} />
                </div>
                <div className="festive-body">
                  <h3>{box.name}</h3>
                  <p className="festive-tagline">{box.tagline}</p>
                  <ul className="festive-items">
                    {box.items.map(({ product, qty }) => (
                      <li key={product.id}>{qty}× {product.name}</li>
                    ))}
                  </ul>
                  <div className="festive-footer">
                    <b>Rs. {box.total.toLocaleString()}</b>
                    <div className="festive-actions">
                      <button className="button ghost small" onClick={() => addFestiveBox(box)} data-testid={`festive-add-${box.id}`}>
                        Add to box
                      </button>
                      <button className="button primary small" onClick={() => whatsappBox(box)} data-testid={`festive-order-${box.id}`}>
                        Order <MessageCircle size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="box-section" id="box">
          <div className="box-heading">
            <div>
              <p className="eyebrow">03 / BUILD YOUR OWN BOX</p>
              <h2>Mix &<br /><em>match loaves.</em></h2>
            </div>
            <p>Choose how many of each loaf. We'll wrap them together.</p>
          </div>
          <div className="builder-grid">
            {products.map((p) => (
              <div className="builder-row" key={p.id} data-testid={`builder-row-${p.id}`}>
                <img src={p.image} alt={p.name} />
                <div className="builder-info">
                  <b>{p.name}</b>
                  <small>Rs. {p.price.toLocaleString()} · serves {p.serves}</small>
                </div>
                <div className="builder-qty">
                  <button onClick={() => bumpBuilder(p.id, -1)} data-testid={`builder-minus-${p.id}`} aria-label="decrease"><Minus size={14} /></button>
                  <span data-testid={`builder-qty-${p.id}`}>{builderQtys[p.id] || 0}</span>
                  <button onClick={() => bumpBuilder(p.id, 1)} data-testid={`builder-plus-${p.id}`} aria-label="increase"><Plus size={14} /></button>
                </div>
              </div>
            ))}
          </div>
          <div className="builder-total">
            <span>Your box</span>
            <b data-testid="builder-total">Rs. {builderTotal.toLocaleString()}</b>
          </div>
          <button className="button primary wide" onClick={addBuilderToCart} disabled={!builderItems.length} data-testid="add-builder-to-cart">
            Add this box to cart <ShoppingBag size={17} />
          </button>
        </section>

        <section className="stories" id="stories">
          <div>
            <p className="eyebrow">04 / STORY BEHIND THE BAKE</p>
            <h2>Good things<br /><em>take time.</em></h2>
            <p className="story-lead">
              Every loaf has a mood, a memory, a reason to be shared. Here are a few of ours.
            </p>
            <a className="inline-link" href="https://www.instagram.com/treatsandtemptationbysk/" target="_blank" rel="noreferrer" data-testid="instagram-link">
              See more on Instagram <Instagram size={17} />
            </a>
          </div>
          <div className="story-grid">
            {products.slice(0, 3).map((p) => (
              <article className="story-card" key={p.id}>
                <img src={p.image} alt={p.name} />
                <div>
                  <p className="eyebrow">THE {p.name.toUpperCase()}</p>
                  <p>{p.story}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer>
        <div className="brand">
          <span className="brand-mark">SK</span>
          <span>Treats &<br /><b>Temptation</b></span>
        </div>
        <span>Made with butter, time & a little bit of magic.</span>
        <a href="https://www.instagram.com/treatsandtemptationbysk/" target="_blank" rel="noreferrer" data-testid="footer-instagram">
          @treatsandtemptationbysk <Instagram size={16} />
        </a>
      </footer>

      {cartOpen && (
        <>
          <div className="drawer-scrim" onClick={() => setCartOpen(false)} data-testid="cart-scrim" />
          <aside className="cart-drawer" data-testid="cart-drawer" role="dialog" aria-label="Your bake box">
            <div className="cart-header">
              <div>
                <p className="eyebrow">YOUR BAKE BOX</p>
                <b>{cartCount ? `${cartCount} loaf${cartCount === 1 ? "" : "s"} chosen` : "Nothing in the box yet"}</b>
              </div>
              <button onClick={() => setCartOpen(false)} data-testid="close-cart" aria-label="Close cart">
                <X />
              </button>
            </div>
            <div className="cart-body">
              {cart.length === 0 ? (
                <div className="cart-empty" data-testid="cart-empty-state">
                  <p>Your box is empty. Find a match, add a festive box, or build your own — it'll land right here.</p>
                </div>
              ) : (
                cart.map((i) => (
                  <div className="cart-row" key={i.id} data-testid={`cart-item-${i.id}`}>
                    <img src={i.image} alt={i.name} />
                    <div className="cart-row-info">
                      <b>{i.name}</b>
                      <small>Rs. {i.price.toLocaleString()} each</small>
                      <div className="cart-qty">
                        <button onClick={() => updateQty(i.id, -1)} data-testid={`cart-qty-minus-${i.id}`}><Minus size={13} /></button>
                        <span data-testid={`cart-qty-${i.id}`}>{i.qty}</span>
                        <button onClick={() => updateQty(i.id, 1)} data-testid={`cart-qty-plus-${i.id}`}><Plus size={13} /></button>
                      </div>
                    </div>
                    <div className="cart-row-right">
                      <strong>Rs. {(i.qty * i.price).toLocaleString()}</strong>
                      <button className="cart-remove" onClick={() => removeFromCart(i.id)} data-testid={`cart-remove-${i.id}`} aria-label="Remove">
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
            {cart.length > 0 && (
              <div className="cart-footer">
                <div className="cart-total">
                  <span>Total</span>
                  <b data-testid="cart-total">Rs. {cartTotal.toLocaleString()}</b>
                </div>
                <button className="button primary wide" onClick={whatsappOrder} data-testid="cart-whatsapp-order">
                  Order via WhatsApp <MessageCircle size={16} />
                </button>
                <button className="cart-clear" onClick={clearCart} data-testid="cart-clear">Clear box</button>
              </div>
            )}
          </aside>
        </>
      )}

      {chatOpen && (
        <div className="chat-drawer" data-testid="baker-chat-drawer">
          <div className="chat-header">
            <div>
              <p className="eyebrow">AI BAKER CHAT</p>
              <b>Ask SK anything sweet</b>
            </div>
            <button onClick={() => setChatOpen(false)} data-testid="close-baker-chat"><X /></button>
          </div>
          <div className="chat-messages">
            {chat.map((m, i) => (
              <div className={`chat-bubble ${m.role}`} key={i} data-testid={`chat-message-${i}`}>{m.text}</div>
            ))}
            {chatLoading && <div className="chat-bubble assistant" data-testid="chat-loading">Kneading a thought…</div>}
          </div>
          {chatError && <div className="chat-error" data-testid="chat-error">{chatError}</div>}
          <div className="chat-input">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendChat()}
              placeholder="e.g. something for 8 people, budget 2000…"
              data-testid="baker-chat-input"
            />
            <button onClick={sendChat} data-testid="send-baker-chat"><ArrowRight /></button>
          </div>
          <button className="whatsapp-button" onClick={whatsappOrder} data-testid="chat-whatsapp-order">
            Order through WhatsApp <MessageCircle size={16} />
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
