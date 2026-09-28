import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { api } from "@/state/api";
import { useCart } from "@/state/CartContext";

const PACK_LABELS = {
  "plain-white": "Plain white box",
  "white-ribbon": "White box with white ribbon",
  "pink-ribbon": "White box with pink ribbon",
};

const PACKAGING_FALLBACK = [
  { id: "plain-white", name: "Plain White Box", price: 100, ribbon: null },
  { id: "white-ribbon", name: "White Box with White Ribbon", price: 150, ribbon: "white" },
  { id: "pink-ribbon", name: "White Box with Pink Ribbon", price: 150, ribbon: "pink" },
];

export default function Checkout() {
  const { items, packagingId, message, setPackaging, setMessage, clearCart } = useCart();
  const [packagings, setPackagings] = useState(PACKAGING_FALLBACK);
  const [form, setForm] = useState({
    name: "", phone: "", address: "", email: "", delivery_date: "", notes: "",
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/packaging").then((r) => setPackagings(r.data)).catch(() => {});
  }, []);

  const subtotal = useMemo(() => items.reduce((n, i) => n + i.qty * i.price, 0), [items]);
  const pack = packagings.find((p) => p.id === packagingId);
  const packPrice = pack?.price || 0;
  const total = subtotal + packPrice;

  const update = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const validate = () => {
    const e = {};
    if (!form.name.trim()) e.name = "We need a name for the order.";
    if (!form.phone.trim() || form.phone.trim().length < 6) e.phone = "Please share a phone number SK can reach.";
    if (!form.address.trim() || form.address.trim().length < 4) e.address = "Please share the delivery address.";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const place = async () => {
    setServerError("");
    if (!items.length) return;
    if (!validate()) return;
    setSubmitting(true);
    try {
      const payload = {
        items: items.map((i) => ({ product_id: i.id, qty: i.qty, custom_box: !!i.custom_box })),
        packaging_id: packagingId || null,
        personalized_message: message || null,
        customer: {
          name: form.name.trim(),
          phone: form.phone.trim(),
          address: form.address.trim(),
          email: form.email.trim() || null,
          delivery_date: form.delivery_date || null,
          notes: form.notes.trim() || null,
        },
      };
      const r = await api.post("/orders", payload);
      clearCart();
      navigate(`/order/${r.data.order_number}`);
    } catch (err) {
      setServerError(err?.response?.data?.detail || "Something went wrong placing your order. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!items.length) {
    return (
      <div className="checkout-empty">
        <p className="eyebrow">YOUR BOX IS EMPTY</p>
        <h1>Let's pick something<br /><em>sweet first.</em></h1>
        <div className="checkout-empty-actions">
          <Link to="/menu" className="button primary" data-testid="checkout-empty-menu">Browse menu</Link>
          <Link to="/build" className="button ghost" data-testid="checkout-empty-build">Build a box</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <header className="checkout-header">
        <p className="eyebrow">CHECKOUT</p>
        <h1>Almost there.<br /><em>Just the details.</em></h1>
      </header>

      <div className="checkout-layout">
        <div className="checkout-form">
          <h2 className="section-h">Where should it go?</h2>
          <div className="form-grid">
            <div className="field">
              <label>Your name</label>
              <input value={form.name} onChange={(e) => update("name", e.target.value)} data-testid="checkout-name" />
              {errors.name && <small className="err">{errors.name}</small>}
            </div>
            <div className="field">
              <label>Phone (WhatsApp)</label>
              <input value={form.phone} onChange={(e) => update("phone", e.target.value)} data-testid="checkout-phone" placeholder="e.g. 03xx xxxxxxx" />
              {errors.phone && <small className="err">{errors.phone}</small>}
            </div>
            <div className="field full">
              <label>Delivery address</label>
              <textarea rows={3} value={form.address} onChange={(e) => update("address", e.target.value)} data-testid="checkout-address" />
              {errors.address && <small className="err">{errors.address}</small>}
            </div>
            <div className="field">
              <label>Delivery date</label>
              <input type="date" value={form.delivery_date} onChange={(e) => update("delivery_date", e.target.value)} data-testid="checkout-date" />
            </div>
            <div className="field">
              <label>Email (optional)</label>
              <input value={form.email} onChange={(e) => update("email", e.target.value)} data-testid="checkout-email" />
            </div>
            <div className="field full">
              <label>Anything else? (optional)</label>
              <textarea rows={2} value={form.notes} onChange={(e) => update("notes", e.target.value)} data-testid="checkout-notes" placeholder="Allergies, special requests, gift notes…" />
            </div>
          </div>

          <h2 className="section-h">Packaging</h2>
          <div className="pack-options">
            {packagings.map((p) => (
              <button
                key={p.id}
                className={`pack-option ${packagingId === p.id ? "active" : ""}`}
                onClick={() => setPackaging(p.id)}
                data-testid={`checkout-pack-${p.id}`}
              >
                <span className={`pack-swatch pack-swatch-${p.id}`} />
                <span>
                  <b>{p.name}</b>
                  <small>+ Rs. {p.price}</small>
                </span>
              </button>
            ))}
          </div>

          <h2 className="section-h">Personalized note</h2>
          <textarea
            className="checkout-message"
            maxLength={140}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            data-testid="checkout-message"
            placeholder="A little something to write on the box (optional)."
          />
          <small className="counter">{message.length}/140</small>

          {serverError && <p className="inline-error" data-testid="checkout-error">{serverError}</p>}
          <button className="button primary wide" onClick={place} disabled={submitting} data-testid="place-order-button">
            {submitting ? "Placing your order…" : <>Place order <ArrowRight size={17} /></>}
          </button>
          <p className="pay-hint"><ShieldCheck size={14} /> Payment via bank transfer — SK will confirm your order & share account details on WhatsApp.</p>
        </div>

        <aside className="checkout-summary">
          <p className="eyebrow">ORDER SUMMARY</p>
          {items.map((i) => (
            <div className="summary-row" key={(i.custom_box ? "c-" : "") + i.id}>
              <img src={i.image} alt={i.name} />
              <div>
                <b>{i.qty}× {i.name}{i.custom_box ? " (single)" : ""}</b>
                <small>Rs. {i.price.toLocaleString()} each</small>
              </div>
              <strong>Rs. {(i.qty * i.price).toLocaleString()}</strong>
            </div>
          ))}
          <div className="summary-line"><span>Subtotal</span><b data-testid="summary-subtotal">Rs. {subtotal.toLocaleString()}</b></div>
          {pack && <div className="summary-line"><span>{pack.name}</span><b data-testid="summary-pack">Rs. {pack.price}</b></div>}
          <div className="summary-line total"><span>Total</span><b data-testid="summary-total">Rs. {total.toLocaleString()}</b></div>
          {message && <p className="summary-message" data-testid="summary-message">"{message}"</p>}
        </aside>
      </div>
    </div>
  );
}
