import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ShoppingBag, WandSparkles, Clock, Sparkles } from "lucide-react";
import { api } from "@/state/api";
import { useCart } from "@/state/CartContext";
import PackModal from "@/components/PackModal";

const CATEGORY_ORDER = ["loaf", "cheesecake", "batch", "cookie"];
const CATEGORY_LABEL = {
  loaf: "Loaves — freshly baked, made with love",
  cheesecake: "Cheesecake & Dessert Boxes",
  batch: "Brownies, Bakes & Dessert Cups",
  cookie: "Artisanal Cookies",
};
const CATEGORY_EYEBROW = {
  loaf: "01 / LOAVES",
  cheesecake: "02 / CHEESECAKE & DESSERT BOXES",
  batch: "03 / BROWNIES, BAKES & CUPS",
  cookie: "04 / COOKIES",
};

export default function Menu() {
  const [products, setProducts] = useState([]);
  const [filter, setFilter] = useState("all");
  const [selectedVariants, setSelectedVariants] = useState({});
  const [packModalProduct, setPackModalProduct] = useState(null);
  const { addItem, setCartOpen } = useCart();

  useEffect(() => {
    api
      .get("/products")
      .then((r) => {
        setProducts(r.data);
        // Pre-initialize default variants for products with variants
        const initVars = {};
        r.data.forEach((p) => {
          if (p.variants && p.variants.length > 0) {
            initVars[p.id] = p.variants[0];
          }
        });
        setSelectedVariants(initVars);
      })
      .catch(() => setProducts([]));
  }, []);

  const grouped = useMemo(() => {
    const g = {};
    CATEGORY_ORDER.forEach((c) => (g[c] = []));
    products.forEach((p) => {
      if (g[p.category]) g[p.category].push(p);
    });
    return g;
  }, [products]);

  const healthyProducts = useMemo(
    () => products.filter((p) => p.healthy),
    [products]
  );

  const addStandard = (p) => {
    const variant = selectedVariants[p.id] || (p.variants ? p.variants[0] : null);
    addItem({
      id: p.id,
      name: p.name,
      price: p.price,
      image: p.image,
      selected_variant: variant,
      custom_box: false,
    });
    setCartOpen(true);
  };

  const openPackCustomizer = (p) => {
    setPackModalProduct(p);
  };

  const handlePackConfirm = (selection) => {
    if (!packModalProduct) return;
    addItem({
      id: packModalProduct.id,
      name: packModalProduct.name,
      price: packModalProduct.price,
      image: packModalProduct.image,
      pack_selection: selection,
      custom_box: false,
    });
    setPackModalProduct(null);
    setCartOpen(true);
  };

  return (
    <div className="menu-page">
      {/* 24 Hours Notice Banner */}
      <div className="notice-banner" data-testid="notice-banner">
        <Clock size={16} className="notice-icon" />
        <span>
          <strong>24 Hours Notice Required</strong> • Freshly prepared & baked to order with love.
        </span>
      </div>

      <header className="menu-header">
        <p className="eyebrow">THE FULL MENU</p>
        <h1>
          Freshly baked,
          <br />
          <em>made with love.</em>
        </h1>
        <p className="menu-lead">
          Browse the whole kitchen — artisanal loaves, dessert boxes, batches, cookies, and wholesome healthy treats.
          Or, for a customized small mix,{" "}
          <Link to="/build" className="inline-link light" data-testid="menu-build-link">
            build a custom box <WandSparkles size={14} />
          </Link>
          .
        </p>

        <div className="menu-filters">
          <button
            className={filter === "all" ? "chip active" : "chip"}
            onClick={() => setFilter("all")}
            data-testid="filter-all"
          >
            All
          </button>
          {CATEGORY_ORDER.map((c) => (
            <button
              key={c}
              className={filter === c ? "chip active" : "chip"}
              onClick={() => setFilter(c)}
              data-testid={`filter-${c}`}
            >
              {CATEGORY_LABEL[c].split(" — ")[0]}
            </button>
          ))}
          <button
            className={filter === "healthy" ? "chip active chip-healthy" : "chip chip-healthy"}
            onClick={() => setFilter("healthy")}
            data-testid="filter-healthy"
          >
            🌿 Healthy Range
          </button>
        </div>
      </header>

      {/* When filtering by Healthy Range */}
      {filter === "healthy" ? (
        <section className="menu-cat" id="cat-healthy">
          <div className="menu-cat-head">
            <p className="eyebrow">SPECIAL COLLECTION</p>
            <h2>Wholesome Healthy Range</h2>
          </div>
          <div className="menu-grid">
            {healthyProducts.map((p) => renderCard(p))}
          </div>
        </section>
      ) : (
        /* Regular category sections */
        (filter === "all" ? CATEGORY_ORDER : [filter]).map((cat) => (
          <section className="menu-cat" key={cat} id={`cat-${cat}`}>
            <div className="menu-cat-head">
              <p className="eyebrow">{CATEGORY_EYEBROW[cat]}</p>
              <h2>{CATEGORY_LABEL[cat]}</h2>
            </div>
            <div className="menu-grid">
              {grouped[cat]?.map((p) => renderCard(p))}
            </div>
          </section>
        ))
      )}

      {/* Pack of 4 Customizer Modal */}
      {packModalProduct && (
        <PackModal
          product={packModalProduct}
          onClose={() => setPackModalProduct(null)}
          onConfirm={handlePackConfirm}
        />
      )}
    </div>
  );

  function renderCard(p) {
    const isPack = !!p.pack_size;
    const currentVariant = selectedVariants[p.id] || (p.variants ? p.variants[0] : null);

    return (
      <article className="menu-card" key={p.id} data-testid={`menu-item-${p.id}`}>
        <div className="menu-card-image">
          <img src={p.image} alt={p.name} />
          {p.healthy && <span className="pill-healthy">Healthy option</span>}
          {isPack && <span className="pill-pack">Pack of {p.pack_size}</span>}
        </div>
        <div className="menu-card-body">
          <h3>{p.name}</h3>
          {p.note && <p className="menu-note">{p.note}</p>}
          <p className="menu-story">"{p.story}"</p>

          {/* Interactive Variant Selection (e.g. Cheesecake toppings) */}
          {p.variants && p.variants.length > 0 && (
            <div className="menu-variant-block">
              <span className="variant-label">Choice of topping:</span>
              <div className="variant-chips">
                {p.variants.map((v) => (
                  <button
                    key={v}
                    type="button"
                    className={`chip-mini ${currentVariant === v ? "active" : ""}`}
                    onClick={() => setSelectedVariants((prev) => ({ ...prev, [p.id]: v }))}
                    data-testid={`variant-${p.id}-${v.replace(/\s+/g, "-").toLowerCase()}`}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Flavors hint for packs */}
          {p.flavors && p.flavors.length > 0 && (
            <p className="menu-flavors-hint">
              <span>Flavours:</span> {p.flavors.join(" · ")}
            </p>
          )}

          {p.addons?.length > 0 && (
            <p className="menu-addon">
              Add {p.addons.map((a) => `${a.name} +Rs. ${a.price}`).join(", ")}
            </p>
          )}

          <div className="menu-card-footer">
            <div>
              <b>Rs. {p.price?.toLocaleString()}</b>
              <small>{p.unit}</small>
            </div>
            {isPack ? (
              <button
                className="button primary small"
                onClick={() => openPackCustomizer(p)}
                data-testid={`menu-customize-${p.id}`}
              >
                Customize Pack <Sparkles size={14} />
              </button>
            ) : (
              <button
                className="button primary small"
                onClick={() => addStandard(p)}
                data-testid={`menu-add-${p.id}`}
              >
                Add <ShoppingBag size={14} />
              </button>
            )}
          </div>
        </div>
      </article>
    );
  }
}
