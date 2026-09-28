import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Gift, Minus, Plus, ShoppingBag, Trash2 } from "lucide-react";
import { api } from "@/state/api";
import { useCart } from "@/state/CartContext";
import { flyToBox } from "@/lib/flyToBox";

const RIBBONS = [
  { id: "clear-box", label: "Clear Plastic Box", price: 150, ribbon: "pink", style: "clear",
    image: "https://customer-assets-rejwkqb3.emergentagent.net/job_bake-moment/artifacts/byzd23k4_2981-Pastry-Box-9-x-6.webp" },
  { id: "white-box", label: "White Cardboard Box", price: 150, ribbon: "pink", style: "white",
    image: "https://customer-assets-rejwkqb3.emergentagent.net/job_bake-moment/artifacts/ww1p99rw_2666-Brownie-Box-6x6x2.webp" },
  { id: "kraft-box", label: "Brown Kraft Box", price: 150, ribbon: "pink", style: "kraft",
    image: "https://customer-assets-rejwkqb3.emergentagent.net/job_bake-moment/artifacts/98od3myz_2666-1-Brownie-Box-6-x-6-x-2-4-Pcs-.webp" },
];

export default function BuildBox() {
  const [products, setProducts] = useState([]);
  const [selection, setSelection] = useState({}); // {productId: qty}
  const [pack, setPack] = useState("white-box");
  const [message, setMessage] = useState("");
  const boxRef = useRef(null);
  const navigate = useNavigate();
  const { addItem, setPackaging, setMessage: saveCartMessage, setCartOpen } = useCart();

  useEffect(() => {
    api.get("/products").then((r) => setProducts(r.data.filter((p) => p.custom_box_unit))).catch(() => {});
  }, []);

  const bump = (product, delta, srcEl) => {
    const currentQty = selection[product.id] || 0;
    const next = Math.max(0, currentQty + delta);
    setSelection((s) => ({ ...s, [product.id]: next }));
    if (delta > 0 && srcEl && boxRef.current) {
      flyToBox(srcEl, boxRef.current, product.image);
    }
  };

  const chosen = useMemo(
    () => products.filter((p) => (selection[p.id] || 0) > 0).map((p) => ({ ...p, qty: selection[p.id] })),
    [products, selection]
  );
  const itemsCount = useMemo(() => chosen.reduce((n, p) => n + p.qty, 0), [chosen]);
  const itemsTotal = useMemo(() => chosen.reduce((n, p) => n + p.qty * p.custom_box_unit, 0), [chosen]);
  const packOption = RIBBONS.find((r) => r.id === pack);
  const total = itemsTotal + (packOption?.price || 0);

  const ribbonClass = packOption?.ribbon ? `ribbon-${packOption.ribbon}` : "";
  const styleClass = packOption?.style ? `box-style-${packOption.style}` : "";

  const addToCartAndCheckout = () => {
    if (!chosen.length) return;
    chosen.forEach((p) => {
      addItem({
        id: p.id, name: p.name,
        price: p.custom_box_unit, image: p.image,
        custom_box: true, qty: p.qty,
      });
    });
    setPackaging(pack);
    saveCartMessage(message);
    setCartOpen(false);
    navigate("/checkout");
  };

  return (
    <div className="build-page">
      <header className="build-header">
        <p className="eyebrow">CUSTOM BOX BUILDER</p>
        <h1>Pick, mix,<br /><em>send with love.</em></h1>
        <p>Choose small treats from the kitchen, pick a ribbon, add a personal note — we'll wrap it just so.</p>
      </header>

      <div className="build-layout">
        <div className="build-picker">
          <p className="eyebrow">01 / PICK YOUR MIX</p>
          <div className="picker-grid">
            {products.map((p) => (
              <div className="picker-card" key={p.id} data-testid={`picker-${p.id}`}>
                <img src={p.image} alt={p.name} />
                <div className="picker-body">
                  <b>{p.name}</b>
                  <small>Rs. {p.custom_box_unit.toLocaleString()} each</small>
                </div>
                <div className="picker-qty">
                  <button onClick={(e) => bump(p, -1, e.currentTarget.closest(".picker-card")?.querySelector("img"))} data-testid={`picker-minus-${p.id}`}>
                    <Minus size={13} />
                  </button>
                  <span data-testid={`picker-qty-${p.id}`}>{selection[p.id] || 0}</span>
                  <button onClick={(e) => bump(p, 1, e.currentTarget.closest(".picker-card")?.querySelector("img"))} data-testid={`picker-plus-${p.id}`}>
                    <Plus size={13} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="pack-section">
            <p className="eyebrow">02 / PICK YOUR PACKAGING</p>
            <p className="pack-hint">Every box comes tied with a pink ribbon and, on request, a personal note.</p>
            <div className="pack-options">
              {RIBBONS.map((r) => (
                <button
                  key={r.id}
                  className={`pack-option ${pack === r.id ? "active" : ""}`}
                  onClick={() => setPack(r.id)}
                  data-testid={`pack-${r.id}`}
                >
                  <img src={r.image} alt={r.label} className="pack-photo" />
                  <span>
                    <b>{r.label}</b>
                    <small>+ Rs. {r.price} · pink ribbon included</small>
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="message-section">
            <p className="eyebrow">03 / ADD A PERSONAL NOTE</p>
            <textarea
              maxLength={140}
              placeholder="e.g. Happy birthday, favourite person."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              data-testid="build-message"
            />
            <small>{message.length}/140</small>
          </div>
        </div>

        <aside className="build-preview">
          <p className="eyebrow">YOUR BOX</p>
          <div className={`preview-box ${ribbonClass} ${styleClass}`} ref={boxRef} data-testid="preview-box">
            <div className="preview-lid" />
            <div className="preview-body">
              {chosen.length === 0 ? (
                <div className="preview-empty">
                  <Gift size={24} />
                  <p>Pick a treat on the left — we'll drop it in here.</p>
                </div>
              ) : (
                <div className="preview-items" data-testid="preview-items">
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
            {packOption?.ribbon && <div className={`preview-ribbon preview-ribbon-${packOption.ribbon}`} data-testid="preview-ribbon" />}
            {message && (
              <div className="preview-tag" data-testid="preview-tag">
                <span>{message}</span>
              </div>
            )}
          </div>

          <div className="preview-summary">
            <div className="preview-row"><span>Items ({itemsCount})</span><b data-testid="preview-items-total">Rs. {itemsTotal.toLocaleString()}</b></div>
            <div className="preview-row"><span>{packOption?.label}</span><b data-testid="preview-pack-total">Rs. {packOption?.price || 0}</b></div>
            <div className="preview-row total"><span>Total</span><b data-testid="preview-total">Rs. {total.toLocaleString()}</b></div>
          </div>

          <button
            className="button primary wide"
            disabled={!chosen.length}
            onClick={addToCartAndCheckout}
            data-testid="build-checkout"
          >
            {chosen.length ? <>Continue to checkout <ArrowRight size={17} /></> : "Add at least one treat"}
          </button>
          <Link to="/menu" className="preview-link">or browse the full menu →</Link>
        </aside>
      </div>
    </div>
  );
}
