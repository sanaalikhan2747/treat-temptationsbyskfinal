import { Link, NavLink } from "react-router-dom";
import { MessageCircle, ShoppingBag } from "lucide-react";
import { useCart } from "@/state/CartContext";

export default function Nav({ onOpenChat }) {
  const { cartCount, setCartOpen } = useCart();
  return (
    <nav className="nav">
      <Link to="/" className="brand" data-testid="brand-home">
        <img src="/logo.svg" alt="Treats & Temptation by SK" className="brand-logo" />
        <span className="brand-text">Treats &<br /><b>Temptation</b></span>
      </Link>
      <div className="nav-links">
        <NavLink to="/menu" data-testid="nav-menu">Menu</NavLink>
        <NavLink to="/build" data-testid="nav-build">Build a box</NavLink>
        <NavLink to="/#festive" data-testid="nav-festive">Festive boxes</NavLink>
        <NavLink to="/#match" data-testid="nav-match">Find your loaf</NavLink>
      </div>
      <button className="icon-button" onClick={onOpenChat} data-testid="open-baker-chat" aria-label="Open baker chat">
        <MessageCircle size={21} />
      </button>
      <button className="cart-pill" onClick={() => setCartOpen(true)} data-testid="cart-button" aria-label="Open cart">
        <ShoppingBag size={18} />
        <span data-testid="cart-count">{cartCount}</span>
      </button>
    </nav>
  );
}
