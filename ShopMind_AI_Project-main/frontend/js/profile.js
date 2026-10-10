// Buyer Profile, AI Preferences, Order History, and Smart Compromise Controller

const prefKey = "shopmind_preferences";
const form = document.getElementById("preferencesForm");
const fields = ["budget", "categories", "brands", "priorities"];

function formatInr(val) {
  const n = Number(val);
  return val == null || !Number.isFinite(n) ? "Not listed" : `₹${n.toLocaleString("en-IN")}`;
}

function renderProfileData() {
  const user = getCurrentUser();

  // Header display
  document.getElementById("userNameDisplay").textContent = user.name || "Valued Buyer";
  document.getElementById("userEmailDisplay").textContent = user.email || "buyer@shopmind.ai";
  if (user.avatar) {
    document.getElementById("userAvatar").textContent = user.avatar;
  }

  // Load form fields from user.preferences
  const prefs = user.preferences || {};
  fields.forEach(k => {
    const el = document.getElementById(k);
    if (el && prefs[k] != null) {
      el.value = prefs[k];
    }
  });

  // Render Stats
  const orders = user.orders || [];
  const searches = user.search_history || [];
  document.getElementById("orderCountStat").textContent = orders.length;
  document.getElementById("searchCountStat").textContent = searches.length;
  const countHeader = document.getElementById("orderCountHeader");
  if (countHeader) countHeader.textContent = `${orders.length} items`;

  // Render Search History
  const searchContainer = document.getElementById("searchHistoryContainer");
  searchContainer.replaceChildren();
  if (!searches.length) {
    searchContainer.innerHTML = `<span style="font-size:11px;color:var(--muted)">No search history yet. Try searching in Products or Chat!</span>`;
  } else {
    searches.forEach(s => {
      const q = typeof s === "object" ? s.query : s;
      const tag = document.createElement("button");
      tag.type = "button";
      tag.className = "search-tag";
      tag.innerHTML = `<span>⌕</span> ${q}`;
      tag.title = "Ask AI in Chat";
      tag.onclick = () => {
        window.location.href = `chat.html?q=${encodeURIComponent(q)}`;
      };
      searchContainer.appendChild(tag);
    });
  }

  // Render Order History
  const orderContainer = document.getElementById("orderListContainer");
  orderContainer.replaceChildren();
  if (!orders.length) {
    orderContainer.innerHTML = `<div style="font-size:12px;color:var(--muted);padding:10px 0;">No orders placed yet. Click "+ Place Test Order" to test!</div>`;
  } else {
    orders.forEach(o => {
      const item = document.createElement("div");
      item.className = "order-item";

      const img = document.createElement("img");
      img.className = "order-thumb";
      img.src = o.image_url || "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=400&q=80";
      img.alt = o.name;

      const info = document.createElement("div");
      info.className = "order-info";
      info.innerHTML = `
        <b>${o.name}</b>
        <small>${o.category} · Ordered on ${o.date || "Recent"}</small>
      `;

      const price = document.createElement("div");
      price.className = "order-price";
      price.textContent = formatInr(o.price);

      item.append(img, info, price);
      orderContainer.appendChild(item);
    });
  }

  // Load and Render AI Recommendations (Requirement 3)
  loadAIRecommendations(orders, searches, prefs);
}

async function loadAIRecommendations(orders, searches, prefs) {
  const container = document.getElementById("aiRecommendationsContainer");
  container.innerHTML = `<div class="empty-state">Synthesizing personalized AI recommendations from your order history and searches...</div>`;

  try {
    const analysis = await fetchBuyerRecommendations(orders, searches, prefs);

    // Update Persona
    if (analysis.persona) {
      document.getElementById("aiPersonaBadge").textContent = `AI Persona: ${analysis.persona}`;
    }
    if (analysis.persona_description) {
      document.getElementById("personaDesc").textContent = analysis.persona_description;
    }
    if (analysis.top_categories?.length) {
      document.getElementById("aiRecBannerText").textContent =
        `Curated specifically for your preferences in ${analysis.top_categories.join(", ")}. Analyzed ${analysis.total_orders_analyzed} past purchase(s) and ${analysis.total_searches_analyzed} search query(s).`;
    }

    const recs = analysis.recommendations || [];
    container.replaceChildren();

    if (!recs.length) {
      container.innerHTML = `<div class="empty-state">Browse the catalogue or place an order to get personalized recommendations!</div>`;
      return;
    }

    recs.forEach(p => {
      const card = document.createElement("article");
      card.className = "product-card";

      const visual = document.createElement("div");
      visual.className = "product-visual";
      visual.appendChild(createProductImage(p, "product-image"));

      const cat = document.createElement("div");
      cat.className = "product-category";
      cat.textContent = p.category || "Product";

      const name = document.createElement("h3");
      name.textContent = p.name;

      const brand = document.createElement("div");
      brand.className = "product-brand";
      brand.textContent = p.brand || "";

      // AI Reason Tag
      const reasonChip = document.createElement("span");
      reasonChip.className = "ai-reason-chip";
      reasonChip.textContent = `✦ ${p.ai_recommendation_reason || "Matches your shopping profile"}`;

      const desc = document.createElement("p");
      desc.className = "product-description";
      desc.textContent = p.description || "";

      const bottom = document.createElement("div");
      bottom.className = "product-bottom";
      bottom.innerHTML = `
        <div class="product-price">${formatInr(p.price)}</div>
        <div class="product-rating">★ ${p.rating || "4.5"}</div>
      `;

      const actions = document.createElement("div");
      actions.className = "product-actions";

      const buyBtn = document.createElement("button");
      buyBtn.className = "primary-small";
      buyBtn.textContent = "Buy Product";
      buyBtn.onclick = () => {
        recordUserOrder(p);
        alert(`Order placed for ${p.name}! Your AI profile and order history have been updated.`);
        renderProfileData();
      };

      const askBtn = document.createElement("button");
      askBtn.textContent = "Ask AI";
      askBtn.onclick = () => {
        window.location.href = `chat.html?q=Tell me more about ${encodeURIComponent(p.name)}`;
      };

      actions.append(buyBtn, askBtn);
      card.append(visual, cat, name, brand, reasonChip, desc, bottom, actions);
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Failed loading AI recommendations", err);
    container.innerHTML = `<div class="empty-state">Could not load AI recommendations. Try refreshing.</div>`;
  }
}

// Preferences Save Form
form.addEventListener("submit", e => {
  e.preventDefault();
  const user = getCurrentUser();
  if (!user.preferences) user.preferences = {};
  fields.forEach(k => {
    user.preferences[k] = document.getElementById(k).value;
  });
  setCurrentUser(user);
  const status = document.getElementById("saveStatus");
  status.textContent = "Preferences saved! Updating AI recommendations...";
  renderProfileData();
  setTimeout(() => { status.textContent = ""; }, 2500);
});

// Reset Preferences
document.getElementById("resetPreferences").addEventListener("click", () => {
  const user = getCurrentUser();
  user.preferences = { budget: 50000, categories: "Laptop", brands: "", priorities: "value" };
  setCurrentUser(user);
  form.reset();
  renderProfileData();
});

// Clear Search History
document.getElementById("clearSearchHistory").addEventListener("click", () => {
  const user = getCurrentUser();
  user.search_history = [];
  setCurrentUser(user);
  renderProfileData();
});

// Simulate Order placement button for testing
document.getElementById("btnSimulateOrder").addEventListener("click", async () => {
  const catalogue = await loadDemoProducts();
  const randomProduct = catalogue[Math.floor(Math.random() * catalogue.length)];
  recordUserOrder(randomProduct);
  alert(`Added simulated order for "${randomProduct.name}" (${randomProduct.category})! Watch how the AI recommendations update.`);
  renderProfileData();
});

// SMART BUDGET & FEATURE COMPROMISE FINDER (Requirement 4)
document.getElementById("btnFindCompromise").addEventListener("click", async () => {
  const category = document.getElementById("compCategory").value;
  const budget = Number(document.getElementById("compBudget").value) || 50000;
  const featuresText = document.getElementById("compFeatures").value;
  const features = featuresText.split(",").map(s => s.trim()).filter(Boolean);

  const resultWrap = document.getElementById("compromiseResultWrap");
  const explanationDiv = document.getElementById("compromiseExplanation");
  const grid = document.getElementById("compromiseProductsGrid");

  resultWrap.style.display = "block";
  explanationDiv.innerHTML = "<em>Analyzing catalogue and calculating smart compromises...</em>";
  grid.replaceChildren();

  try {
    let compromiseData;
    if (typeof DEMO_MODE !== "undefined" && !DEMO_MODE) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/smart-budget-compromise`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ category, max_budget: budget, requested_features: features })
        });
        if (res.ok) compromiseData = await res.json();
      } catch (e) {}
    }

    if (!compromiseData) {
      compromiseData = await localSmartCompromise(category, budget, features);
    }

    const explanation = compromiseData.explanation || compromiseData.answer;
    explanationDiv.innerHTML = explanation.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");

    const products = compromiseData.compromise_products || compromiseData.products || [];
    grid.replaceChildren();

    products.forEach(p => {
      const card = document.createElement("article");
      card.className = "product-card";

      const visual = document.createElement("div");
      visual.className = "product-visual";
      visual.appendChild(createProductImage(p, "product-image"));

      const badge = document.createElement("span");
      badge.className = "ai-reason-chip";
      badge.style.background = "#eefbf3";
      badge.style.color = "#15803d";
      badge.textContent = `✓ Budget Match (Under ₹${budget.toLocaleString('en-IN')})`;

      const cat = document.createElement("div");
      cat.className = "product-category";
      cat.textContent = p.category || "Product";

      const name = document.createElement("h3");
      name.textContent = p.name;

      const desc = document.createElement("p");
      desc.className = "product-description";
      desc.textContent = p.description || "";

      const bottom = document.createElement("div");
      bottom.className = "product-bottom";
      bottom.innerHTML = `
        <div class="product-price">${formatInr(p.price)}</div>
        <div class="product-rating">★ ${p.rating || "4.5"}</div>
      `;

      card.append(visual, badge, cat, name, desc, bottom);
      grid.appendChild(card);
    });
  } catch (err) {
    explanationDiv.textContent = "Error calculating compromise. Please try again.";
  }
});

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  renderProfileData();
});
