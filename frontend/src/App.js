import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { ArrowRight, Instagram, MessageCircle, Minus, Plus, ShoppingBag, Sparkles, Trash2, WandSparkles, X } from "lucide-react";
import "@/App.css";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const occasions = ["Birthday", "Tea party", "Gift", "Anniversary", "Family gathering", "Just craving something"];
const moods = ["Chocolate lover", "Fresh & citrusy", "Warm & comforting", "Coffee lover", "Something different"];

const BOX_MIX = [
  { id: "banana-loaf", qty: 1, label: "loaf" },
  { id: "cookie-jar", qty: 2, label: "cookies" },
  { id: "brownies", qty: 2, label: "brownies" },
  { id: "cinnamon-rolls", qty: 1, label: "cinnamon roll" },
];

function slug(x) { return x.toLowerCase().replaceAll(" ", "-").replaceAll("&", "and"); }

function App() {
  const [products, setProducts] = useState([]);
  const [occasion, setOccasion] = useState("Tea party");
  const [mood, setMood] = useState("Warm & comforting");
  const [people, setPeople] = useState(6);
  const [budget, setBudget] = useState(1000);
  const [dietary, setDietary] = useState("No preference");
  const [match, setMatch] = useState(null);
  const [matchError, setMatchError] = useState("");
  const [loading, setLoading] = useState(false);
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [chatError, setChatError] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chat, setChat] = useState([
    { role: "assistant", text: "Tell me who you’re baking for, and I’ll find the sweet spot." },
  ]);

  useEffect(() => {
    axios.get(`${API}/products`).then((r) => setProducts(r.data)).catch(() => setProducts([]));
  }, []);

  const productById = useMemo(() => Object.fromEntries(products.map((p) => [p.id, p])), [products]);
  const cartCount = useMemo(() => cart.reduce((n, i) => n + i.qty, 0), [cart]);
  const cartTotal = useMemo(() => cart.reduce((n, i) => n + i.qty * i.price, 0), [cart]);
  const boxItems = useMemo(
    () => BOX_MIX.map((m) => ({ ...m, product: productById[m.id] })).filter((m) => m.product),
    [productById]
  );
  const boxTotal = useMemo(
    () => boxItems.reduce((n, m) => n + m.qty * m.product.price, 0),
    [boxItems]
  );

  const addToCart = (product, qty = 1) => {
    setCart((items) => {
      const existing = items.find((i) => i.id === product.id);
      if (existing) return items.map((i) => (i.id === product.id ? { ...i, qty: i.qty + qty } : i));
      return [...items, { id: product.id, name: product.name, price: product.price, image: product.image, qty }];
    });
    setCartOpen(true);
  };
  const addBoxToCart = () => {
    setCart((items) => {
      const next = [...items];
      boxItems.forEach(({ product, qty }) => {
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
      explanation: `${picked.name} — a little baker's instinct says this is the one you didn't know you were craving.`,
    });
    setTimeout(() => document.getElementById("match-result")?.scrollIntoView({ behavior: "smooth" }), 60);
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
      text = `Hello Treats & Temptation by SK!\nI'd like to order: ${match.product.name} — Rs. ${match.product.price.toLocaleString()}.`;
    } else {
      text = `Hello Treats & Temptation by SK! I'd like to place an order.`;
    }
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank");
  };

  return (
    <div className="site-shell">
      <nav className="nav">
        <a className="brand" href="#top" data-testid="brand-home">
          <span className="brand-mark">SK</span>
          <span>Treats &<br /><b>Temptation</b></span>
        </a>
        <div className="nav-links">
          <a href="#match" data-testid="nav-match">Find your bake</a>
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
            <p className="eyebrow">HOMEMADE, MATCHED TO THE MOMENT</p>
            <h1>Find the bake<br /><em>you feel like.</em></h1>
            <p className="hero-text">
              Not sure what to order? Tell us the occasion, the mood and who's coming.
              We'll make the sweet decision easy.
            </p>
            <div className="hero-actions">
              <a href="#match" className="button primary" data-testid="hero-find-bake">
                Find my perfect bake <ArrowRight size={17} />
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
              src="https://images.unsplash.com/photo-1700448293876-07dca826c161?auto=format&fit=crop&w=1300&q=85"
              alt="Homemade chocolate cake"
              data-testid="hero-dessert-image"
            />
            <div className="image-stamp">made for<br /><b>your moment</b></div>
          </div>
        </section>

        <section className="match-section" id="match">
          <div className="section-intro">
            <p className="eyebrow">01 / THE DESSERT MATCHMAKER</p>
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
                <div className="result-meta">
                  <span>Serves {match.product.serves}</span>
                  <b>Rs. {match.product.price.toLocaleString()}</b>
                </div>
                <button className="button primary" onClick={() => addToCart(match.product)} data-testid="add-match-to-cart">
                  Add to my box <ShoppingBag size={17} />
                </button>
              </div>
            </div>
          </section>
        )}

        <section className="box-section" id="box">
          <div className="box-heading">
            <div>
              <p className="eyebrow">02 / BUILD YOUR BOX</p>
              <h2>A little bit of<br /><em>everything.</em></h2>
            </div>
            <p>Choose your mix. We'll do the wrapping.</p>
          </div>
          <div className="box-layout">
            <div className="box-visual">
              <div className="box-label">YOUR<br /><b>BAKE BOX</b></div>
              <div className="box-items">
                {boxItems.map((m, i) => (
                  <div className={`box-piece piece-${i}`} key={m.id}>
                    <img src={m.product.image} alt={m.product.name} />
                    <span>{m.qty}×</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="box-list">
              {boxItems.map((m) => (
                <div className="box-row" key={m.id} data-testid={`box-row-${m.id}`}>
                  <img src={m.product.image} alt={m.product.name} />
                  <div>
                    <b>{m.qty}× {m.product.name}</b>
                    <small>handmade in small batches</small>
                  </div>
                  <strong>Rs. {(m.qty * m.product.price).toLocaleString()}</strong>
                </div>
              ))}
              <div className="box-total">
                <span>Box total</span>
                <b data-testid="box-total">Rs. {boxTotal.toLocaleString()}</b>
              </div>
              <button className="button primary wide" onClick={addBoxToCart} data-testid="add-box-to-cart">
                Add this box to cart <ShoppingBag size={17} />
              </button>
            </div>
          </div>
        </section>

        <section className="stories" id="stories">
          <div>
            <p className="eyebrow">03 / STORY BEHIND THE BAKE</p>
            <h2>Good things<br /><em>take time.</em></h2>
            <p className="story-lead">
              Every bake has a mood, a memory, a reason to be shared. Here are a few of ours.
            </p>
            <a className="inline-link" href="https://www.instagram.com/treatsandtemptationbysk/" target="_blank" rel="noreferrer" data-testid="instagram-link">
              See more on Instagram <Instagram size={17} />
            </a>
          </div>
          <div className="story-grid">
            {products.slice(1, 4).map((p) => (
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
                <b>{cartCount ? `${cartCount} bake${cartCount === 1 ? "" : "s"} chosen` : "Nothing in the box yet"}</b>
              </div>
              <button onClick={() => setCartOpen(false)} data-testid="close-cart" aria-label="Close cart">
                <X />
              </button>
            </div>
            <div className="cart-body">
              {cart.length === 0 ? (
                <div className="cart-empty" data-testid="cart-empty-state">
                  <p>Your box is empty. Find a match or build a box, and it will land right here.</p>
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
              placeholder="e.g. something for 8 people…"
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
