import { createContext, useContext, useEffect, useMemo, useState } from "react";

const CartContext = createContext(null);

const STORAGE_KEY = "tt_cart_v1";

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
      const key = item.custom_box ? `${item.id}::cbox` : item.id;
      const existing = s.items.find((i) => (i.custom_box ? `${i.id}::cbox` : i.id) === key);
      const nextItems = existing
        ? s.items.map((i) => ((i.custom_box ? `${i.id}::cbox` : i.id) === key ? { ...i, qty: i.qty + (item.qty || 1) } : i))
        : [...s.items, { ...item, qty: item.qty || 1 }];
      return { ...s, items: nextItems };
    });
  };

  const setQty = (key, qty) => setState((s) => ({
    ...s,
    items: s.items.map((i) => ((i.custom_box ? `${i.id}::cbox` : i.id) === key ? { ...i, qty: Math.max(1, qty) } : i)),
  }));

  const removeItem = (key) => setState((s) => ({
    ...s,
    items: s.items.filter((i) => (i.custom_box ? `${i.id}::cbox` : i.id) !== key),
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
