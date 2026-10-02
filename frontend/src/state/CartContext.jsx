import { createContext, useContext, useEffect, useMemo, useState } from "react";

const CartContext = createContext(null);

const STORAGE_KEY = "tt_cart_v1";

export function getItemKey(item) {
  if (!item) return "";
  if (item.cartKey) return item.cartKey;
  if (item.custom_box) return `${item.id}::cbox`;
  if (item.pack_selection) {
    const sorted = Object.entries(item.pack_selection)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}:${v}`)
      .join("|");
    return `${item.id}::pack::${sorted}`;
  }
  if (item.selected_variant) return `${item.id}::var::${item.selected_variant}`;
  return item.id;
}

function loadInitial() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return { items: [], packagingId: null, message: "" };
}

export function CartProvider({ children }) {
  const [state, setState] = useState(loadInitial);
  const [cartOpen, setCartOpen] = useState(false);

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch {}
  }, [state]);

  const addItem = (item) => {
    setState((s) => {
      const key = getItemKey(item);
      const existing = s.items.find((i) => getItemKey(i) === key);
      const nextItems = existing
        ? s.items.map((i) => (getItemKey(i) === key ? { ...i, qty: i.qty + (item.qty || 1) } : i))
        : [...s.items, { ...item, cartKey: key, qty: item.qty || 1 }];
      return { ...s, items: nextItems };
    });
  };

  const setQty = (key, qty) => setState((s) => ({
    ...s,
    items: s.items.map((i) => (getItemKey(i) === key ? { ...i, qty: Math.max(1, qty) } : i)),
  }));

  const removeItem = (key) => setState((s) => ({
    ...s,
    items: s.items.filter((i) => getItemKey(i) !== key && i.id !== key),
  }));

  const clearCart = () => setState({ items: [], packagingId: null, message: "" });

  const setPackaging = (id) => setState((s) => ({ ...s, packagingId: id }));
  const setMessage = (msg) => setState((s) => ({ ...s, message: msg }));

  const cartCount = useMemo(() => state.items.reduce((n, i) => n + i.qty, 0), [state.items]);
  const subtotal = useMemo(() => state.items.reduce((n, i) => n + i.qty * i.price, 0), [state.items]);

  const value = {
    ...state,
    cartOpen, setCartOpen,
    addItem, setQty, removeItem, clearCart, setPackaging, setMessage,
    cartCount, subtotal,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used inside CartProvider");
  return ctx;
}
