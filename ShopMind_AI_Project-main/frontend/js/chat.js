const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatMessages = document.getElementById("chatMessages");
const note = document.getElementById("connectionNote");

if (note) {
  note.textContent = (typeof DEMO_MODE !== "undefined" && DEMO_MODE)
    ? "Demo mode · Local sample products; switch DEMO_MODE off in config.js to connect to the FastAPI backend."
    : "Connected mode · Powered by ShopMind AI & Catalogue.";
}

// Display a chat message
function addMessage(text, isUser = false, isCompromise = false) {
  const row = document.createElement("div");
  row.className = "message-row" + (isUser ? " user-message" : "");

  const bubble = document.createElement("div");
  bubble.className = "bubble" + (isCompromise ? " compromise-bubble" : "");
  
  if (isCompromise) {
    bubble.style.borderLeft = "4px solid #16a34a";
    bubble.style.background = "#f0fdf4";
    bubble.style.color = "#14532d";
  }

  bubble.innerHTML = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");

  row.appendChild(bubble);
  chatMessages.appendChild(row);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  return bubble;
}

// Format product prices in Indian rupees
function formatPrice(value) {
  const n = Number(value);
  return value == null || !Number.isFinite(n)
    ? "Not listed"
    : `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

// Display product cards
function addProducts(products, isCompromise = false) {
  if (!products?.length) return;

  const grid = document.createElement("div");
  grid.className = "inline-products";

  products.forEach((p) => {
    const card = document.createElement("div");
    card.className = "mini-product";

    if (p.image_url) {
      const img = document.createElement("img");
      img.src = p.image_url;
      img.alt = p.name || "Product image";
      img.loading = "lazy";
      img.style.cssText = "width:100%;height:96px;object-fit:cover;border-radius:8px;margin-bottom:8px";
      img.onerror = () => { img.style.display = "none"; };
      card.appendChild(img);
    }

    if (p.is_compromise || isCompromise) {
      const compBadge = document.createElement("span");
      compBadge.style.cssText = "display:inline-block;background:#dcfce7;color:#15803d;font-size:9px;font-weight:800;padding:2px 6px;border-radius:4px;margin-bottom:4px;";
      compBadge.textContent = "💡 AI BUDGET FIT";
      card.appendChild(compBadge);
    }

    const title = document.createElement("b");
    title.textContent = p.name || "Product";

    const price = document.createElement("span");
    price.textContent = formatPrice(p.price);

    const rating = document.createElement("span");
    rating.className = "product-rating";
    rating.textContent = p.rating != null ? `★ ${Number(p.rating).toFixed(1)}/5` : "Rating not listed";

    card.append(title, price, rating);

    if (p.comparison?.rank) {
      const rank = document.createElement("span");
      rank.className = "comparison-rank";
      rank.textContent = `#${p.comparison.rank} · Value score ${p.comparison.value_score ?? "—"}`;
      card.appendChild(rank);
    }

    // Quick Action button in chat
    const orderBtn = document.createElement("button");
    orderBtn.style.cssText = "margin-top:8px;width:100%;padding:5px;font-size:10px;font-weight:700;background:var(--purple);color:white;border:none;border-radius:6px;cursor:pointer;";
    orderBtn.textContent = "Order Item";
    orderBtn.onclick = () => {
      if (typeof recordUserOrder === "function") {
        recordUserOrder(p);
        alert(`Order placed for ${p.name}! Your buyer profile and AI preferences have been updated.`);
      }
    };
    card.appendChild(orderBtn);

    grid.appendChild(card);
  });

  chatMessages.appendChild(grid);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Display the product comparison table
function addComparisonTable(products, comparison) {
  if (!products?.length || !comparison) return;

  const wrap = document.createElement("div");
  wrap.className = "comparison-wrap";

  const heading = document.createElement("h3");
  heading.className = "comparison-heading";
  heading.textContent = "Product comparison";
  wrap.appendChild(heading);

  const hint = document.createElement("p");
  hint.className = "comparison-hint";
  hint.textContent = "Value score = 70% rating + 30% affordability relative to the products shown.";
  wrap.appendChild(hint);

  const scroll = document.createElement("div");
  scroll.className = "comparison-scroll";

  const table = document.createElement("table");
  table.className = "comparison-table";

  const thead = document.createElement("thead");
  const header = document.createElement("tr");

  ["Product", "Price", "Rating", "Value score", "Verdict"].forEach((label) => {
    const th = document.createElement("th");
    th.textContent = label;
    header.appendChild(th);
  });

  thead.appendChild(header);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  const cheapestId = comparison.cheapest_product_id;
  const highestId = comparison.highest_rated_product_id;
  const bestId = comparison.best_value_product_id;

  products.forEach((p) => {
    const tr = document.createElement("tr");

    const name = document.createElement("td");
    name.textContent = p.name || "Product";

    const price = document.createElement("td");
    price.textContent = formatPrice(p.price);

    const rating = document.createElement("td");
    rating.textContent = p.rating != null ? `★ ${Number(p.rating).toFixed(1)}/5` : "Not rated";

    const score = document.createElement("td");
    score.textContent = p.comparison?.value_score != null ? `${p.comparison.value_score}/100` : "—";

    const verdict = document.createElement("td");
    const tags = [];
    if (p.product_id === bestId) tags.push("Best value");
    if (p.product_id === cheapestId) tags.push("Lowest price");
    if (p.product_id === highestId) tags.push("Top rating");
    verdict.textContent = tags.join(" · ") || "Alternative";

    if (p.product_id === bestId) tr.className = "best-value-row";

    [name, price, rating, score, verdict].forEach((td) => { tr.appendChild(td); });
    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  scroll.appendChild(table);
  wrap.appendChild(scroll);

  chatMessages.appendChild(wrap);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show product results directly; use text replies only when there are no products.
async function submitMessage(message) {
  if (!message.trim()) return;

  addMessage(message, true);

  try {
    const result = await sendChatMessage(message);
    const products = result.products || [];
    const isCompromise = result.response_type === "budget_compromise" || result.is_compromise;

    if (result.answer) {
      addMessage(result.answer, false, isCompromise);
    }

    if (result.response_type === "comparison" && result.comparison) {
      addComparisonTable(products, result.comparison);
    }

    if (products.length) {
      addProducts(products, isCompromise);
    } else if (!result.answer) {
      addMessage("No matching products found. Try adjusting your search query or category.");
    }
  } catch (e) {
    addMessage("Could not reach the backend. Check that the server is running.");
    console.error(e);
  }
}

// Handle the chat form
if (chatForm) {
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    chatInput.value = "";
    submitMessage(message);
  });
}

// Handle suggested prompt buttons
document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    submitMessage(button.dataset.prompt);
  });
});

// Auto-run query if passed in URL query param (?q=...)
document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const q = params.get("q");
  if (q) {
    setTimeout(() => { submitMessage(q); }, 200);
  }
});
