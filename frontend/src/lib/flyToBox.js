// Animates a clone of `sourceEl` toward the box element (`targetEl`).
export function flyToBox(sourceEl, targetEl, imageUrl) {
  if (!sourceEl || !targetEl) return;
  const src = sourceEl.getBoundingClientRect();
  const dst = targetEl.getBoundingClientRect();
  const clone = document.createElement("img");
  clone.src = imageUrl;
  clone.className = "flying-item";
  const startX = src.left + src.width / 2;
  const startY = src.top + src.height / 2;
  const endX = dst.left + dst.width / 2;
  const endY = dst.top + dst.height / 2;
  clone.style.left = `${startX - 32}px`;
  clone.style.top = `${startY - 32}px`;
  document.body.appendChild(clone);
  requestAnimationFrame(() => {
    clone.style.transform = `translate(${endX - startX}px, ${endY - startY}px) scale(0.25) rotate(18deg)`;
    clone.style.opacity = "0.15";
  });
  const cleanup = () => clone.remove();
  clone.addEventListener("transitionend", cleanup, { once: true });
  setTimeout(cleanup, 900);
  // pulse the target
  targetEl.classList.remove("box-pulse");
  void targetEl.offsetWidth;
  targetEl.classList.add("box-pulse");
}
