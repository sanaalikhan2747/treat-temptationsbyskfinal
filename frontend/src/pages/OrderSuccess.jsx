import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { CheckCircle2, Copy, MessageCircle } from "lucide-react";
import { api, waLink } from "@/state/api";

export default function OrderSuccess() {
  const { orderNumber } = useParams();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.get(`/orders/${orderNumber}`).then((r) => setOrder(r.data)).catch(() => setError("We couldn't find that order."));
  }, [orderNumber]);

  const waMessage = order && (() => {
    const lines = order.items.map((i) => {
      let line = `• ${i.qty}× ${i.name}${i.custom_box ? " (single)" : ""}`;
      if (i.selected_variant) {
        line += ` [Topping: ${i.selected_variant}]`;
      }
      if (i.pack_selection) {
        const packSummary = Object.entries(i.pack_selection)
          .map(([fl, c]) => `${c}× ${fl}`)
          .join(", ");
        line += ` [${packSummary}]`;
      }
      line += ` — Rs. ${i.line_total.toLocaleString()}`;
      return line;
    }).join("\n");

    const parts = [
      `Hello Treats & Temptation by SK!`,
      `New order ${order.order_number}`,
      `Name: ${order.customer.name}`,
      `Phone: ${order.customer.phone}`,
      `Address: ${order.customer.address}`,
    ];
    if (order.customer.delivery_date) parts.push(`Delivery: ${order.customer.delivery_date}`);
    parts.push("", "Items:", lines);
    if (order.packaging) parts.push("", `Packaging: ${order.packaging.name} (Rs. ${order.packaging.price})`);
    if (order.personalized_message) parts.push(`Note on box: "${order.personalized_message}"`);
    if (order.customer.notes) parts.push(`Notes: ${order.customer.notes}`);
    parts.push("", `Total: Rs. ${order.total.toLocaleString()}`, "", `Please confirm & share bank details for payment. Thank you!`);
    return parts.join("\n");
  })();

  const copyOrder = async () => {
    if (!waMessage) return;
    try {
      await navigator.clipboard.writeText(waMessage);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  if (error) {
    return (
      <div className="success-page">
        <h1>Hmm, we couldn't find that order.</h1>
        <p>Please check the link or <Link to="/menu">browse the menu</Link>.</p>
      </div>
    );
  }
  if (!order) return <div className="success-page"><p>Fetching your order…</p></div>;

  return (
    <div className="success-page">
      <div className="success-badge"><CheckCircle2 size={26} /></div>
      <p className="eyebrow">ORDER RECEIVED</p>
      <h1>Thank you, {order.customer.name.split(" ")[0]}.<br /><em>Your box is on the way.</em></h1>
      <p className="success-lead">
        Your order number is <b data-testid="order-number">{order.order_number}</b>. To finalise, tap "Send to SK on WhatsApp" — SK will confirm and share bank transfer details.
      </p>

      <div className="success-actions">
        <a
          className="button primary wide"
          href={waLink(waMessage)}
          target="_blank"
          rel="noreferrer"
          data-testid="order-whatsapp"
        >
          Send to SK on WhatsApp <MessageCircle size={17} />
        </a>
        <button className="button ghost" onClick={copyOrder} data-testid="order-copy">
          {copied ? "Copied!" : <>Copy order details <Copy size={14} /></>}
        </button>
      </div>

      <div className="success-summary">
        <h3>Order summary</h3>
        {order.items.map((i, idx) => (
          <div className="summary-row plain" key={(i.custom_box ? "c-" : "") + i.product_id + "-" + idx}>
            <img src={i.image} alt={i.name} />
            <div>
              <b>{i.qty}× {i.name}{i.custom_box ? " (single)" : ""}</b>
              {i.selected_variant && (
                <span className="summary-spec">Topping: {i.selected_variant}</span>
              )}
              {i.pack_selection && (
                <span className="summary-spec">
                  {Object.entries(i.pack_selection).map(([fl, c]) => `${c}× ${fl}`).join(", ")}
                </span>
              )}
              <small>Rs. {i.unit_price.toLocaleString()} each</small>
            </div>
            <strong>Rs. {i.line_total.toLocaleString()}</strong>
          </div>
        ))}
        <div className="summary-line"><span>Subtotal</span><b>Rs. {order.subtotal.toLocaleString()}</b></div>
        {order.packaging && <div className="summary-line"><span>{order.packaging.name}</span><b>Rs. {order.packaging.price}</b></div>}
        <div className="summary-line total"><span>Total</span><b data-testid="order-total">Rs. {order.total.toLocaleString()}</b></div>
        {order.personalized_message && (
          <p className="summary-message">"{order.personalized_message}"</p>
        )}
        <div className="success-customer">
          <b>{order.customer.name}</b>
          <span>{order.customer.phone}</span>
          <span>{order.customer.address}</span>
          {order.customer.delivery_date && <span>Delivery: {order.customer.delivery_date}</span>}
        </div>
      </div>
    </div>
  );
}
