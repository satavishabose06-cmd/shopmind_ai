let demoProductsPromise;

function createProductImage(product, className) {
  if (!product.image_url) {
    return Object.assign(document.createElement("span"), {
      className: `${className}-unavailable`,
      textContent: "Image unavailable"
    });
  }
  const image = document.createElement("img");
  image.className = className;
  image.alt = `${product.name || "Product"} product image`;
  image.loading = "lazy";
  image.decoding = "async";
  image.src = product.image_url;
  image.addEventListener("error", () => {
    image.replaceWith(Object.assign(document.createElement("span"), {
      className: `${className}-unavailable`,
      textContent: "Image unavailable"
    }));
  });
  return image;
}

async function loadDemoProducts() {
  if (!demoProductsPromise) {
    const url = new URL("../data/sample_products.json", window.location.href);
    demoProductsPromise = fetch(url).then(response => {
      if (!response.ok) throw new Error(`Sample catalogue: ${response.status}`);
      return response.json();
    }).then(products => {
      if (!Array.isArray(products)) throw new Error("Sample catalogue must be a JSON array.");
      return products;
    });
  }
  return demoProductsPromise;
}

async function fetchProducts(params = {}) {
  if (typeof DEMO_MODE !== "undefined" && DEMO_MODE) {
    let list = [...await loadDemoProducts()];
    if (params.category) list = list.filter(p => p.category.toLowerCase() === String(params.category).toLowerCase());
    if (params.search) {
      const q = String(params.search).toLowerCase();
      list = list.filter(p => `${p.name} ${p.brand} ${p.category} ${p.description}`.toLowerCase().includes(q));
    }
    if (params.max_price != null) list = list.filter(p => p.price <= Number(params.max_price));
    return list;
  }
  
  try {
    const query = new URLSearchParams(params);
    const r = await fetch(`${API_BASE_URL}/api/products?${query}`);
    if (r.ok) return r.json();
  } catch (e) {
    console.warn("Backend not reached, using local sample products", e);
  }
  
  // Fallback to local catalogue
  let list = [...await loadDemoProducts()];
  if (params.category) list = list.filter(p => p.category.toLowerCase() === String(params.category).toLowerCase());
  if (params.search) {
    const q = String(params.search).toLowerCase();
    list = list.filter(p => `${p.name} ${p.brand} ${p.category} ${p.description}`.toLowerCase().includes(q));
  }
  if (params.max_price != null) list = list.filter(p => p.price <= Number(params.max_price));
  return list;
}

function parsePriceConstraints(message) {
  const pattern = /(not\s+less\s+than|less\s+than|under|below|cheaper\s+than|within|up\s*to|at\s+most|maximum|max(?:imum)?|budget(?:\s+of)?|not\s+more\s+than|not\s+exceed(?:ing)?|greater\s+than|more\s+than|above|over|at\s+least|minimum|min(?:imum)?)\s*(?:₹|rs\.?\s*|inr\s*)?([\d,]+(?:\.\d+)?)\s*([kl]?)/gi;
  return [...message.matchAll(pattern)].map(([, operatorText, amountText, suffix]) => {
    const operator = operatorText.toLowerCase().replace(/\s+/g, " ");
    const amount = Number((Number(amountText.replace(/,/g, "")) * (suffix.toLowerCase() === "k" ? 1000 : suffix.toLowerCase() === "l" ? 100000 : 1)).toFixed(2));
    if (["less than", "cheaper than"].includes(operator)) return { operator: "lt", amount };
    if (["under", "below", "within", "up to", "at most", "maximum", "max", "budget", "budget of", "not more than", "not exceeding"].includes(operator)) return { operator: "le", amount };
    if (["greater than", "more than", "above", "over"].includes(operator)) return { operator: "gt", amount };
    return { operator: "ge", amount };
  });
}

function extractFeatures(message) {
  const q = message.toLowerCase();
  const feats = [];
  if (q.includes("32gb") || q.includes("32 gb")) feats.push("32GB RAM");
  else if (q.includes("16gb") || q.includes("16 gb")) feats.push("16GB RAM");
  else if (q.includes("12gb") || q.includes("12 gb")) feats.push("12GB RAM");

  if (q.includes("1tb") || q.includes("1 tb")) feats.push("1TB Storage");
  else if (q.includes("512gb") || q.includes("512 gb")) feats.push("512GB Storage");

  if (q.includes("i7") || q.includes("core i7")) feats.push("Core i7");
  if (q.includes("ryzen 7")) feats.push("Ryzen 7");
  if (q.includes("4k") || q.includes("ultra hd")) feats.push("4K Display");
  if (q.includes("noise cancel") || q.includes("anc")) feats.push("Noise Cancelling");
  return feats;
}

// Client-side fallback for Smart Budget Compromise
async function localSmartCompromise(category, maxBudget, requestedFeatures) {
  const catalogue = await loadDemoProducts();
  const catProducts = category ? catalogue.filter(p => p.category.toLowerCase() === category.toLowerCase()) : catalogue;
  
  const budgetProducts = catProducts.filter(p => p.price <= maxBudget).sort((a, b) => (b.rating || 0) - (a.rating || 0));
  const premiumMatches = catProducts.filter(p => {
    const text = `${p.name} ${p.description} ${JSON.stringify(p.specifications || {})}`.toLowerCase();
    return requestedFeatures.some(f => text.includes(f.toLowerCase().replace(" ", "")));
  });

  const minPremiumPrice = premiumMatches.length ? Math.min(...premiumMatches.map(p => p.price)) : null;
  const topAlternative = budgetProducts[0] || catProducts[0];

  const compromiseProducts = (budgetProducts.length ? budgetProducts.slice(0, 4) : catProducts.slice(0, 3)).map(p => ({
    ...p,
    is_compromise: true,
    compromise_badge: `Budget Fit (Under ₹${maxBudget.toLocaleString('en-IN')})`
  }));

  const featureText = requestedFeatures.length ? requestedFeatures.join(", ") : "extra premium features";
  const explanation = `💡 **AI Smart Budget Compromise Found:**\n\nYou asked for ${category || "a product"} with **${featureText}** under **₹${maxBudget.toLocaleString("en-IN")}**.\n\n${minPremiumPrice ? `Products with all those exact high-tier specs start at **₹${minPremiumPrice.toLocaleString("en-IN")}** in our catalogue.\n\n` : ""}To fit **100% within your budget of ₹${maxBudget.toLocaleString("en-IN")}**, here are the best value alternatives with balanced features (such as **${topAlternative.name}** at **₹${topAlternative.price?.toLocaleString("en-IN")}** with rating **${topAlternative.rating}/5**) instead of leaving you empty-handed!`;

  return {
    is_compromise: true,
    answer: explanation,
    products: compromiseProducts,
    requested_features: requestedFeatures,
    max_budget: maxBudget,
    response_type: "budget_compromise"
  };
}

async function sendChatMessage(message) {
  // Record search history for logged in user
  if (typeof recordUserSearch === "function") {
    recordUserSearch(message);
  }

  // Try FastAPI backend first
  if (typeof DEMO_MODE !== "undefined" && !DEMO_MODE) {
    try {
      const user = (typeof getCurrentUser === "function") ? getCurrentUser() : { user_id: "demo-user" };
      const r = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, user_id: user.user_id || "demo-user" })
      });
      if (r.ok) return await r.json();
    } catch (e) {
      console.warn("Backend chat failed, running smart client-side assistant...", e);
    }
  }

  // Smart Client-side Assistant with Budget Compromise
  const q = message.trim().toLowerCase().replace(/[!. ]+$/g, "");
  if (/^(hi+|hello|hey|good morning|good afternoon|good evening)$/.test(q)) {
    return {
      answer: "Hi! I'm ShopMind AI. Tell me what product you're looking for, your budget, or specific features you need. If any feature is above your budget, I'll find you the best value compromise!",
      products: [],
      response_type: "greeting"
    };
  }
  if (/^(bye+|goodbye|good bye|see you|take care)$/.test(q)) {
    return {
      answer: "Goodbye! Thanks for shopping with ShopMind AI. Have a wonderful day!",
      products: [],
      response_type: "farewell"
    };
  }

  const constraints = parsePriceConstraints(message);
  const requestedFeatures = extractFeatures(message);
  let category = null;
  if (q.includes("laptop") || q.includes("macbook")) category = "Laptop";
  else if (q.includes("phone") || q.includes("smartphone")) category = "Phone";
  else if (q.includes("headphone") || q.includes("earbuds") || q.includes("audio")) category = "Headphones";
  else if (q.includes("monitor") || q.includes("display")) category = "Monitor";
  else if (q.includes("keyboard")) category = "Keyboard";
  else if (q.includes("mouse")) category = "Mouse";
  else if (q.includes("watch") || q.includes("smartwatch")) category = "Smartwatch";
  else if (q.includes("camera")) category = "Camera";
  else if (q.includes("speaker")) category = "Speaker";
  else if (q.includes("tablet") || q.includes("ipad")) category = "Tablet";

  let list = [...await loadDemoProducts()];
  if (category) list = list.filter(p => p.category === category);
  
  // Strict matching
  let matched = list;
  if (constraints.length) {
    matched = matched.filter(p => constraints.every(({ operator, amount }) =>
      operator === "lt" ? p.price < amount :
      operator === "le" ? p.price <= amount :
      operator === "gt" ? p.price > amount :
      p.price >= amount
    ));
  }
  if (requestedFeatures.length) {
    matched = matched.filter(p => {
      const text = `${p.name} ${p.description} ${JSON.stringify(p.specifications || {})}`.toLowerCase();
      return requestedFeatures.some(f => text.includes(f.toLowerCase().replace(" ", "")));
    });
  }

  // REQUIREMENT 4: If no product matches budget + extra features, execute smart compromise!
  if (!matched.length && (constraints.length || requestedFeatures.length)) {
    let maxBudget = 60000;
    const le = constraints.find(c => c.operator === "le" || c.operator === "lt");
    if (le) maxBudget = le.amount;
    return await localSmartCompromise(category, maxBudget, requestedFeatures);
  }

  if (!matched.length) {
    matched = list.slice(0, 4);
  }

  matched.sort((a, b) => (b.rating || 0) - (a.rating || 0));
  const top = matched.slice(0, 4);
  return {
    answer: `I found ${top.length} great option(s) for you. ${top[0].name} (₹${top[0].price?.toLocaleString('en-IN')}, ★${top[0].rating}/5) is my top recommendation based on your requirements!`,
    products: top,
    response_type: "products"
  };
}

// REQUIREMENT 3: AI Buyer Preferences & Recommendations API
async function fetchBuyerRecommendations(orders = [], searchHistory = [], preferences = {}) {
  if (typeof DEMO_MODE !== "undefined" && !DEMO_MODE) {
    try {
      const r = await fetch(`${API_BASE_URL}/api/recommendations/buyer-profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ orders, search_history: searchHistory, preferences })
      });
      if (r.ok) return await r.json();
    } catch (e) {
      console.warn("Backend buyer recommendations failed, using client AI synthesis...", e);
    }
  }

  // Client-side AI synthesis fallback
  const catalogue = await loadDemoProducts();
  const orderCats = orders.map(o => o.category).filter(Boolean);
  const searchCats = [];
  searchHistory.forEach(s => {
    const q = (typeof s === "object" ? s.query : s).toLowerCase();
    if (q.includes("laptop")) searchCats.push("Laptop");
    if (q.includes("headphone") || q.includes("audio")) searchCats.push("Headphones");
    if (q.includes("monitor")) searchCats.push("Monitor");
    if (q.includes("phone")) searchCats.push("Phone");
    if (q.includes("camera")) searchCats.push("Camera");
  });

  const topCats = [...new Set([...orderCats, ...searchCats])];
  if (!topCats.length) topCats.push(preferences.categories || "Laptop", "Headphones");

  let persona = "Smart Value Explorer";
  let personaDesc = "You focus on high-rated, dependable gear with the best price-to-performance ratio.";
  if (topCats.includes("Laptop") && (topCats.includes("Monitor") || topCats.includes("Keyboard"))) {
    persona = "Workspace & Productivity Builder";
    personaDesc = "You prioritize seamless desktop ergonomics, computing speed, and workflow efficiency.";
  } else if (topCats.includes("Headphones") || topCats.includes("Speaker")) {
    persona = "Audiophile & Creative Enthusiast";
    personaDesc = "You appreciate acoustic precision, noise cancellation, and rich soundstages.";
  }

  const orderedIds = new Set(orders.map(o => o.product_id));
  const recs = catalogue
    .filter(p => !orderedIds.has(p.product_id))
    .filter(p => topCats.includes(p.category))
    .slice(0, 6)
    .map(p => ({
      ...p,
      ai_recommendation_reason: `Recommended based on your affinity for ${p.category}s and recent activity`
    }));

  return {
    persona,
    persona_description: personaDesc,
    top_categories: topCats,
    average_spend: `₹${(preferences.budget || 55000).toLocaleString('en-IN')}`,
    total_orders_analyzed: orders.length,
    total_searches_analyzed: searchHistory.length,
    recommendations: recs
  };
}
