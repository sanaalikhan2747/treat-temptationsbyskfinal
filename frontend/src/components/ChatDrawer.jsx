import { useState } from "react";
import { ArrowRight, MessageCircle, X } from "lucide-react";
import { api, waLink } from "@/state/api";

export default function ChatDrawer({ open, onClose }) {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [chat, setChat] = useState([
    { role: "assistant", text: "Tell me who you're baking for, and I'll pick the loaf that fits the moment." },
  ]);

  const send = async () => {
    if (!message.trim() || loading) return;
    const text = message.trim();
    setMessage("");
    setChat((c) => [...c, { role: "user", text }]);
    setError("");
    setLoading(true);
    try {
      const r = await api.post("/chat", { message: text });
      setChat((c) => [...c, { role: "assistant", text: r.data.reply }]);
      if (r.data.ok === false) setError("Live baker unavailable — showing a friendly fallback.");
    } catch {
      setChat((c) => [...c, { role: "assistant", text: "The oven's a little warm right now — try me again in a moment." }]);
      setError("Live baker unavailable — try again in a moment.");
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;
  return (
    <div className="chat-drawer" data-testid="baker-chat-drawer">
      <div className="chat-header">
        <div>
          <p className="eyebrow">AI BAKER CHAT</p>
          <b>Ask SK anything sweet</b>
        </div>
        <button onClick={onClose} data-testid="close-baker-chat"><X /></button>
      </div>
      <div className="chat-messages">
        {chat.map((m, i) => (
          <div className={`chat-bubble ${m.role}`} key={i} data-testid={`chat-message-${i}`}>{m.text}</div>
        ))}
        {loading && <div className="chat-bubble assistant" data-testid="chat-loading">Kneading a thought…</div>}
      </div>
      {error && <div className="chat-error" data-testid="chat-error">{error}</div>}
      <div className="chat-input">
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="e.g. something for 8 people, budget 2000…"
          data-testid="baker-chat-input"
        />
        <button onClick={send} data-testid="send-baker-chat"><ArrowRight /></button>
      </div>
      <button
        className="whatsapp-button"
        onClick={() => window.open(waLink("Hello Treats & Temptation by SK! I'd like to place an order."), "_blank")}
        data-testid="chat-whatsapp-order"
      >
        Order through WhatsApp <MessageCircle size={16} />
      </button>
    </div>
  );
}
