import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowRight, ChevronDown, Gift, Minus, Plus, Trash2 } from "lucide-react";
import { api } from "@/state/api";
import { useCart } from "@/state/CartContext";
import { flyToBox } from "@/lib/flyToBox";

const RIBBONS = [
  { id: "plain-white", label: "Plain white box", price: 100, ribbon: null },
  { id: "white-ribbon", label: "White ribbon", price: 150, ribbon: "white" },
  { id: "pink-ribbon", label: "Pink ribbon", price: 150, ribbon: "pink" },
];

const CATEGORY_LABEL = { loaf: "Loaves", cheesecake: "Cheesecake & desserts", batch: "Batches", cookie: "Cookies" };
const CATEGORY_ORDER = ["loaf", "cheesecake", "batch", "cookie"];

export default function FestiveBoxEditor() {
  const { boxId } = useParams();
  const navigate = useNavigate();
  const [box, setBox] = useState(null);
  const [products, setProducts] = useState([]);
  const [selection, setSelection] = useState({}); // {product_id: qty}
  const [pack, setPack] = useState("pink-ribbon");
  const [message, setMessage] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [addCat, setAddCat] = useState("loaf");
  const boxRef = useRef(null);
  const { addItem, setPackaging, setMessage: saveCartMessage } = useCart();

  useEffect(() => {
    api.get(`/festive-boxes/${boxId}`).then((r) => {
      setBox(r.data);
      const seed = {};
      r.data.items.forEach(({ product, qty }) => { seed[product.id] = qty; });
      setSelection(seed);
    }).catch(() => setBox(null));
    api.get("/products").then((r) => setProducts(r.data)).catch(() => {});
  }, [boxId]);

  const productById = useMemo(() => Object.fromEntries(products.map((p) => [p.id, p])), [products]);

  const chosen = useMemo(
    () => Object.entries(selection)
      .filter(([, qty]) => qty > 0)
      .map(([id, qty]) => ({ ...productById[id], qty }))
      .filter((p) => p.id),
    [selection, productById]
  );
  const itemsCount = useMemo(() => chosen.reduce((n, p) => n + p.qty, 0), [chosen]);
  const itemsTotal = useMemo(() => chosen.reduce((n, p) => n + p.qty * p.price, 0), [chosen]);
  const packOption = RIBBONS.find((r) => r.id === pack);
  const total = itemsTotal + (packOption?.price || 0);
  const ribbonClass = packOption?.ribbon ? `ribbon-${packOption.ribbon}` : "";

  const bump = (product, delta, srcEl) => {
    const currentQty = selection[product.id] || 0;
    const next = Math.max(0, currentQty + delta);
    setSelection((s) => ({ ...s, [product.id]: next }));
    if (delta > 0 && srcEl && boxRef.current) flyToBox(srcEl, boxRef.current, product.image);
  };

  const remove = (id) => setSelection((s) => { const n = { ...s }; delete n[id]; return n; });

  const groupedForAdd = useMemo(() => {
    const g = {};
    CATEGORY_ORDER.forEach((c) => (g[c] = []));
    products.forEach((p) => { if (g[p.category]) g[p.category].push(p); });
    return g;
  }, [products]);

  const addToCart = () => {
    if (!chosen.length) return;
    chosen.forEach((p) => {
      addItem({ id: p.id, name: p.name, price: p.price, image: p.image, custom_box: false, qty: p.qty });
    });
    setPackaging(pack);
    saveCartMessage(message);
    navigate("/checkout");
  };

  if (box === null) return <div className="build-page"><h1>Loading…</h1></div>;
  if (box === false) return <div className="build-page"><h1>Box not found.</h1><Link to="/">Back home</Link></div>;

  return (
    <div className="build-page">
      <header className="build-header">
        <p className="eyebrow">CUSTOMIZE — {box.name.toUpperCase()}</p>
        <h1>Make it<br /><em>truly yours.</em></h1>
        <p>Start from our {box.name} and change anything — add treats, remove items, swap the ribbon.</p>
      </header>

      <div className="build-layout">
        <div className="build-picker">
          <p className="eyebrow">01 / IN YOUR BOX</p>
          {chosen.length === 0 && <p className="empty-note">Your box is empty. Add something from below.</p>}
          <div className="picker-grid">
            {chosen.map((p) => (
              <div className="picker-card" key={p.id} data-testid={`festive-in-${p.id}`}>
                <img src={p.image} alt={p.name} />
                <div className="picker-body">
                  <b>{p.name}</b>
                  <small>Rs. {p.price.toLocaleString()} each</small>
                </div>
                <div className="picker-qty">
                  <button onClick={(e) => bump(p, -1)} data-testid={`festive-minus-${p.id}`}><Minus size={13} /></button>
                  <span data-testid={`festive-qty-${p.id}`}>{p.qty}</span>
                  <button onClick={(e) => bump(p, 1, e.currentTarget.closest(".picker-card")?.querySelector("img"))} data-testid={`festive-plus-${p.id}`}><Plus size={13} /></button>
                </div>
                <button className="picker-remove" onClick={() => remove(p.id)} data-testid={`festive-remove-${p.id}`} aria-label="Remove">
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>

          <button
            className={`add-more-header ${addOpen ? "open" : ""}`}
            onClick={() => setAddOpen((o) => !o)}
            data-testid="festive-add-more-toggle"
          >
            <div>
              <p className="eyebrow">02 / ADD MORE FROM THE MENU</p>
              <b>Loaves, cheesecakes, batches, cookies — anything you like</b>
            </div>
            <ChevronDown size={18} />
          </button>
          {addOpen && (
            <div className="add-more-panel" data-testid="festive-add-panel">
              <div className="add-more-tabs">
                {CATEGORY_ORDER.map((c) => (
                  <button
                    key={c}
                    className={`chip ${addCat === c ? "active" : ""}`}
                    onClick={() => setAddCat(c)}
                    data-testid={`festive-tab-${c}`}
                  >
                    {CATEGORY_LABEL[c]}
                  </button>
                ))}
              </div>
              <div className="picker-grid">
                {groupedForAdd[addCat].map((p) => (
                  <div className="picker-card" key={p.id} data-testid={`festive-add-${p.id}`}>
                    <img src={p.image} alt={p.name} />
                    <div className="picker-body">
                      <b>{p.name}</b>
                      <small>Rs. {p.price.toLocaleString()} {p.unit ? `· ${p.unit}` : ""}</small>
                    </div>
                    <div className="picker-qty">
                      <button onClick={() => bump(p, -1)} data-testid={`festive-add-minus-${p.id}`}><Minus size={13} /></button>
                      <span data-testid={`festive-add-qty-${p.id}`}>{selection[p.id] || 0}</span>
                      <button onClick={(e) => bump(p, 1, e.currentTarget.closest(".picker-card")?.querySelector("img"))} data-testid={`festive-add-plus-${p.id}`}><Plus size={13} /></button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="pack-section">
            <p className="eyebrow">03 / PICK YOUR PACKAGING</p>
            <div className="pack-options">
              {RIBBONS.map((r) => (
                <button
                  key={r.id}
                  className={`pack-option ${pack === r.id ? "active" : ""}`}
                  onClick={() => setPack(r.id)}
                  data-testid={`festive-pack-${r.id}`}
                >
                  <span className={`pack-swatch pack-swatch-${r.id}`} />
                  <span>
                    <b>{r.label}</b>
                    <small>+ Rs. {r.price}</small>
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="message-section">
            <p className="eyebrow">04 / ADD A PERSONAL NOTE</p>
            <textarea
              maxLength={140}
              placeholder={`e.g. Happy ${box.name.replace(" Box", "").toLowerCase()}, favourite person.`}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              data-testid="festive-message"
            />
            <small>{message.length}/140</small>
          </div>
        </div>

        <aside className="build-preview">
          <p className="eyebrow">YOUR BOX</p>
          <div className={`preview-box ${ribbonClass}`} ref={boxRef} data-testid="festive-preview-box">
            <div className="preview-lid" />
            <div className="preview-body">
              {chosen.length === 0 ? (
                <div className="preview-empty">
                  <Gift size={24} />
                  <p>Empty for now — bring it to life on the left.</p>
                </div>
              ) : (
                <div className="preview-items" data-testid="festive-preview-items">
                  {chosen.slice(0, 12).map((p) => (
                    <div className="preview-chip" key={p.id} title={`${p.qty}× ${p.name}`}>
                      <img src={p.image} alt={p.name} />
                      <span>{p.qty}×</span>
                    </div>
                  ))}
                  {chosen.length > 12 && <span className="preview-more">+{chosen.length - 12}</span>}
                </div>
              )}
            </div>
            {packOption?.ribbon && <div className={`preview-ribbon preview-ribbon-${packOption.ribbon}`} data-testid="festive-preview-ribbon" />}
            {message && (
              <div className="preview-tag" data-testid="festive-preview-tag">
                <span>{message}</span>
              </div>
            )}
          </div>

          <div className="preview-summary">
            <div className="preview-row"><span>Items ({itemsCount})</span><b data-testid="festive-items-total">Rs. {itemsTotal.toLocaleString()}</b></div>
            <div className="preview-row"><span>{packOption?.label}</span><b>Rs. {packOption?.price || 0}</b></div>
            <div className="preview-row total"><span>Total</span><b data-testid="festive-total">Rs. {total.toLocaleString()}</b></div>
          </div>

          <button className="button primary wide" disabled={!chosen.length} onClick={addToCart} data-testid="festive-checkout">
            {chosen.length ? <>Continue to checkout <ArrowRight size={17} /></> : "Add something first"}
          </button>
          <Link to="/" className="preview-link">← back to festive boxes</Link>
        </aside>
      </div>
    </div>
  );
}
