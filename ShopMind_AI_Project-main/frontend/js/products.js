const container = document.getElementById("productContainer");
const searchInput = document.getElementById("productSearch");
const categorySelect = document.getElementById("categoryFilter");
const priceSelect = document.getElementById("maxPriceFilter");
const sortSelect = document.getElementById("sortFilter");
const count = document.getElementById("productCount");
const compromiseBox = document.getElementById("smartCompromiseBox");
const btnTriggerCompromise = document.getElementById("btnTriggerCompromise");

let products = [];
const key = "shopmind_compare_ids";

function ids() {
  try {
    return JSON.parse(localStorage.getItem(key) || "[]");
  } catch {
    return [];
  }
}

function render() {
  const q = searchInput.value.trim().toLowerCase();
  const cat = categorySelect.value;
  const maxP = priceSelect && priceSelect.value ? Number(priceSelect.value) : null;

  // Record search in buyer history if search query is present
  if (q.length > 2 && typeof recordUserSearch === "function") {
    recordUserSearch(searchInput.value.trim());
  }

  let list = products.filter(p => {
    const matchCat = !cat || p.category === cat;
    const matchPrice = maxP == null || (p.price != null && p.price <= maxP);
    const text = `${p.name} ${p.brand} ${p.category} ${p.description} ${JSON.stringify(p.specifications || {})}`.toLowerCase();
    const matchSearch = !q || text.includes(q);
    return matchCat && matchPrice && matchSearch;
  });

  if (sortSelect.value === "price-asc") list.sort((a, b) => (a.price ?? Infinity) - (b.price ?? Infinity));
  if (sortSelect.value === "price-desc") list.sort((a, b) => (b.price ?? -Infinity) - (a.price ?? -Infinity));
  if (sortSelect.value === "rating") list.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0));

  count.textContent = `${list.length} product(s) found`;
  container.replaceChildren();

  if (!list.length) {
    if (compromiseBox) compromiseBox.style.display = "flex";
    const e = document.createElement("div");
    e.className = "empty-state";
    e.textContent = "No products match these exact filters. Try our AI Budget Compromise Assistant below!";
    container.append(e);
    return;
  } else {
    if (compromiseBox) compromiseBox.style.display = "none";
  }

  list.forEach(p => {
    const c = document.createElement("article");
    c.className = "product-card";

    const v = document.createElement("div");
    v.className = "product-visual";
    v.append(createProductImage(p, "product-image"));

    const catEl = document.createElement("div");
    catEl.className = "product-category";
    catEl.textContent = p.category || "Product";

    const h = document.createElement("h3");
    h.textContent = p.name || "Unnamed product";

    const brand = document.createElement("div");
    brand.className = "product-brand";
    brand.textContent = p.brand || "";

    const desc = document.createElement("p");
    desc.className = "product-description";
    desc.textContent = p.description || "No description available.";

    const bottom = document.createElement("div");
    bottom.className = "product-bottom";
    const price = document.createElement("div");
    price.className = "product-price";
    price.textContent = p.price != null ? `₹${Number(p.price).toLocaleString("en-IN")}` : "Price unavailable";

    const rating = document.createElement("div");
    rating.className = "product-rating";
    rating.textContent = p.rating != null ? `★ ${p.rating} rating` : "Rating unavailable";
    bottom.append(price, rating);

    const actions = document.createElement("div");
    actions.className = "product-actions";

    const buyBtn = document.createElement("button");
    buyBtn.className = "buy-btn-small";
    buyBtn.textContent = "Buy Item";
    buyBtn.onclick = () => {
      if (typeof recordUserOrder === "function") {
        recordUserOrder(p);
        alert(`Order placed for ${p.name}! Your AI buyer preferences and order history have been updated in your profile.`);
      }
    };

    const cmp = document.createElement("button");
    const selected = ids().includes(String(p.product_id));
    cmp.textContent = selected ? "✓ Added" : "⇄ Compare";
    cmp.className = selected ? "selected" : "";
    cmp.onclick = () => {
      let selectedIds = ids(), id = String(p.product_id);
      selectedIds = selectedIds.includes(id) ? selectedIds.filter(x => x !== id) : [...selectedIds, id];
      localStorage.setItem(key, JSON.stringify(selectedIds));
      render();
    };

    const ask = document.createElement("button");
    ask.className = "primary-small";
    ask.textContent = "Ask AI";
    ask.onclick = () => {
      location.href = `chat.html?q=Tell me about ${encodeURIComponent(p.name)}`;
    };

    actions.append(buyBtn, cmp, ask);
    c.append(v, catEl, h, brand, desc, bottom, actions);
    container.append(c);
  });
}

if (btnTriggerCompromise) {
  btnTriggerCompromise.addEventListener("click", () => {
    const q = searchInput.value.trim();
    const cat = categorySelect.value;
    const maxP = priceSelect.value || "50000";
    const prompt = `I'm looking for a ${cat || "product"} with features ${q || 'good specs'} within budget of ₹${maxP}`;
    window.location.href = `chat.html?q=${encodeURIComponent(prompt)}`;
  });
}

async function init() {
  try {
    products = await fetchProducts();
    const categories = [...new Set(products.map(p => p.category).filter(Boolean))].sort((a, b) => a.localeCompare(b));
    categories.forEach(category => {
      const option = document.createElement("option");
      option.value = category;
      option.textContent = category;
      categorySelect.append(option);
    });
    render();
  } catch (e) {
    container.textContent = "Could not load products. Check the catalogue or backend.";
    count.textContent = "Catalogue unavailable";
    console.error(e);
  }
}

[searchInput, categorySelect, priceSelect, sortSelect].filter(Boolean).forEach(el => el.addEventListener("input", render));
init();
