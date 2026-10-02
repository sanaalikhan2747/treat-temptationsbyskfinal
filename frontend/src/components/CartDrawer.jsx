import { Minus, Plus, ShoppingBag, Trash2, X } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useCart, getItemKey } from "@/state/CartContext";

export default function CartDrawer() {
  const { cartOpen, setCartOpen, items, cartCount, subtotal, setQty, removeItem, clearCart } = useCart();
  const navigate = useNavigate();
  if (!cartOpen) return null;

  return (
    <>
      <div className="drawer-scrim" onClick={() => setCartOpen(false)} data-testid="cart-scrim" />
      <aside className="cart-drawer" data-testid="cart-drawer" role="dialog" aria-label="Your bake box">
        <div className="cart-header">
          <div>
            <p className="eyebrow">YOUR BAKE BOX</p>
            <b>{cartCount ? `${cartCount} item${cartCount === 1 ? "" : "s"} chosen` : "Nothing in the box yet"}</b>
          </div>
          <button onClick={() => setCartOpen(false)} data-testid="close-cart" aria-label="Close cart">
            <X />
          </button>
        </div>
        <div className="cart-body">
          {items.length === 0 ? (
            <div className="cart-empty" data-testid="cart-empty-state">
              <p>Your box is empty. Find a match, add a festive box, or build your own — it'll land right here.</p>
              <Link to="/menu" className="button ghost small" onClick={() => setCartOpen(false)}>Browse menu</Link>
            </div>
          ) : (
            items.map((i) => {
              const k = getItemKey(i);
              return (
                <div className="cart-row" key={k} data-testid={`cart-item-${k}`}>
                  <img src={i.image} alt={i.name} />
                  <div className="cart-row-info">
                    <b>{i.name}{i.custom_box ? " (single)" : ""}</b>

                    {i.selected_variant && (
                      <span className="cart-item-spec" data-testid={`cart-variant-${k}`}>
                        Topping: {i.selected_variant}
                      </span>
                    )}

                    {i.pack_selection && (
                      <span className="cart-item-spec" data-testid={`cart-pack-${k}`}>
                        {Object.entries(i.pack_selection).map(([fl, c]) => `${c}× ${fl}`).join(", ")}
                      </span>
                    )}

                    <small>Rs. {i.price.toLocaleString()} each</small>
                    <div className="cart-qty">
                      <button onClick={() => setQty(k, i.qty - 1)} data-testid={`cart-qty-minus-${k}`} aria-label="Decrease quantity"><Minus size={13} /></button>
                      <span data-testid={`cart-qty-${k}`}>{i.qty}</span>
                      <button onClick={() => setQty(k, i.qty + 1)} data-testid={`cart-qty-plus-${k}`} aria-label="Increase quantity"><Plus size={13} /></button>
                    </div>
                  </div>
                  <div className="cart-row-right">
                    <strong>Rs. {(i.qty * i.price).toLocaleString()}</strong>
                    <button className="cart-remove" onClick={() => removeItem(k)} data-testid={`cart-remove-${k}`} aria-label="Remove">
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
        {items.length > 0 && (
          <div className="cart-footer">
            <div className="cart-total">
              <span>Subtotal</span>
              <b data-testid="cart-subtotal">Rs. {subtotal.toLocaleString()}</b>
            </div>
            <button
              className="button primary wide"
              onClick={() => { setCartOpen(false); navigate("/checkout"); }}
              data-testid="cart-checkout"
            >
              Proceed to checkout <ShoppingBag size={16} />
            </button>
            <button className="cart-clear" onClick={clearCart} data-testid="cart-clear">Clear box</button>
          </div>
        )}
      </aside>
    </>
  );
}
