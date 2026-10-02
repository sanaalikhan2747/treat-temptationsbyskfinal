import { useState, useMemo, useEffect } from "react";
import { X, Plus, Minus, Check, Sparkles } from "lucide-react";

export default function PackModal({ product, onClose, onConfirm }) {
  const flavors = useMemo(() => product?.flavors || [], [product]);
  const packSize = product?.pack_size || 4;

  const [counts, setCounts] = useState(() => {
    const init = {};
    const fl = product?.flavors || [];
    const ps = product?.pack_size || 4;
    fl.forEach((f) => (init[f] = 0));
    if (fl.length === 4) {
      fl.forEach((f) => (init[f] = 1));
    } else if (fl.length === 2) {
      init[fl[0]] = 2;
      init[fl[1]] = 2;
    } else if (fl.length === 3) {
      init[fl[0]] = 2;
      init[fl[1]] = 1;
      init[fl[2]] = 1;
    } else if (fl.length === 1) {
      init[fl[0]] = ps;
    }
    return init;
  });

  // Reset counts when the product changes
  useEffect(() => {
    if (!product) return;
    const init = {};
    const fl = product.flavors || [];
    const ps = product.pack_size || 4;
    fl.forEach((f) => (init[f] = 0));
    if (fl.length === 4) {
      fl.forEach((f) => (init[f] = 1));
    } else if (fl.length === 2) {
      init[fl[0]] = 2;
      init[fl[1]] = 2;
    } else if (fl.length === 3) {
      init[fl[0]] = 2;
      init[fl[1]] = 1;
      init[fl[2]] = 1;
    } else if (fl.length === 1) {
      init[fl[0]] = ps;
    }
    setCounts(init);
  }, [product]);

  const totalSelected = useMemo(
    () => Object.values(counts).reduce((sum, n) => sum + (n || 0), 0),
    [counts]
  );

  const remaining = packSize - totalSelected;
  const isComplete = totalSelected === packSize;

  const updateCount = (flavor, delta) => {
    const current = counts[flavor] || 0;
    const next = current + delta;
    if (next < 0) return;
    if (delta > 0 && totalSelected >= packSize) return;
    setCounts((prev) => ({ ...prev, [flavor]: next }));
  };

  const setAllOneFlavor = (flavor) => {
    const next = {};
    flavors.forEach((f) => (next[f] = f === flavor ? packSize : 0));
    setCounts(next);
  };

  // Build array of chosen items for visual slots
  const slots = useMemo(() => {
    const items = [];
    flavors.forEach((f) => {
      const c = counts[f] || 0;
      for (let i = 0; i < c; i++) {
        items.push(f);
      }
    });
    while (items.length < packSize) {
      items.push(null);
    }
    return items.slice(0, packSize);
  }, [counts, flavors, packSize]);

  if (!product) return null;

  const handleConfirm = () => {
    if (!isComplete) return;
    // Filter only flavors with > 0 count
    const selection = {};
    Object.entries(counts).forEach(([f, c]) => {
      if (c > 0) selection[f] = c;
    });
    onConfirm(selection);
  };

  return (
    <>
      <div className="pack-modal-scrim" onClick={onClose} data-testid="pack-modal-scrim" />
      <div className="pack-modal" role="dialog" aria-modal="true" data-testid="pack-modal">
        <div className="pack-modal-header">
          <div>
            <p className="eyebrow">CUSTOMIZE YOUR PACK OF {packSize}</p>
            <h2>{product.name}</h2>
            <p className="pack-modal-price">
              <b>Rs. {product.price?.toLocaleString()}</b>
              <span>• Choose any {packSize} of the same or different flavours</span>
            </p>
          </div>
          <button className="pack-modal-close" onClick={onClose} aria-label="Close modal" data-testid="pack-modal-close">
            <X size={20} />
          </button>
        </div>

        {/* Visual 4-slot rack */}
        <div className="pack-slots-rack">
          <div className="pack-slots-header">
            <span className="pack-slots-title">
              <Sparkles size={14} /> Box Slots: {totalSelected} of {packSize} filled
            </span>
            <span className={`pack-slots-status ${isComplete ? "complete" : "pending"}`}>
              {isComplete ? (
                <>
                  <Check size={13} /> Ready to pack
                </>
              ) : (
                `Pick ${remaining} more`
              )}
            </span>
          </div>
          <div className="pack-slots-grid">
            {slots.map((item, idx) => (
              <div
                key={idx}
                className={`pack-slot-card ${item ? "filled" : "empty"}`}
                data-testid={`pack-slot-${idx}`}
              >
                <span className="pack-slot-number">#{idx + 1}</span>
                <span className="pack-slot-name">{item || "Empty slot"}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Flavors list with steppers and Quick-Pick */}
        <div className="pack-flavors-list">
          {flavors.map((flavor) => {
            const count = counts[flavor] || 0;
            return (
              <div className="pack-flavor-row" key={flavor} data-testid={`pack-flavor-${flavor}`}>
                <div className="pack-flavor-info">
                  <span className="pack-flavor-title">{flavor}</span>
                  <button
                    type="button"
                    className="pack-quick-all"
                    onClick={() => setAllOneFlavor(flavor)}
                    data-testid={`pack-quick-all-${flavor}`}
                  >
                    All {packSize} of this
                  </button>
                </div>
                <div className="pack-stepper">
                  <button
                    type="button"
                    className="pack-stepper-btn"
                    onClick={() => updateCount(flavor, -1)}
                    disabled={count === 0}
                    data-testid={`pack-minus-${flavor}`}
                    aria-label={`Decrease ${flavor}`}
                  >
                    <Minus size={14} />
                  </button>
                  <span className="pack-stepper-count" data-testid={`pack-count-${flavor}`}>
                    {count}
                  </span>
                  <button
                    type="button"
                    className="pack-stepper-btn"
                    onClick={() => updateCount(flavor, 1)}
                    disabled={totalSelected >= packSize}
                    data-testid={`pack-plus-${flavor}`}
                    aria-label={`Increase ${flavor}`}
                  >
                    <Plus size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Modal footer */}
        <div className="pack-modal-footer">
          <button
            type="button"
            className="button primary wide"
            disabled={!isComplete}
            onClick={handleConfirm}
            data-testid="pack-modal-submit"
          >
            {isComplete
              ? `Add Pack to Box • Rs. ${product.price?.toLocaleString()}`
              : `Select ${remaining} more item${remaining === 1 ? "" : "s"}`}
          </button>
        </div>
      </div>
    </>
  );
}
