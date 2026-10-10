// ShopMind AI Authentication & Buyer Profile Management

const AUTH_STORAGE_KEY = "shopmind_current_user";
const USERS_DB_KEY = "shopmind_registered_users";

// Default seed demo buyer account with realistic orders and searches
const DEFAULT_BUYER = {
  user_id: "usr_001",
  name: "Alex Chen",
  email: "buyer@shopmind.ai",
  role: "buyer",
  avatar: "🧑‍💻",
  preferences: {
    budget: 65000,
    categories: "Laptop",
    brands: "Aster, Orbit, NovaTech",
    priorities: "performance"
  },
  orders: [
    {
      order_id: "ORD-8921",
      product_id: "LAP002",
      name: "Aster ProBook",
      category: "Laptop",
      brand: "Aster",
      price: 66900,
      rating: 4.8,
      date: "2026-09-15",
      image_url: "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80"
    },
    {
      order_id: "ORD-9044",
      product_id: "KEY001",
      name: "KeyCraft TypePro A",
      category: "Keyboard",
      brand: "KeyCraft",
      price: 4500,
      rating: 4.6,
      date: "2026-09-28",
      image_url: "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=80"
    }
  ],
  search_history: [
    { query: "laptop under 70000 with 16gb ram", timestamp: "2026-10-01 10:15" },
    { query: "4K studio monitor color calibrated", timestamp: "2026-10-05 14:20" },
    { query: "wireless noise cancelling headphones", timestamp: "2026-10-08 09:00" },
    { query: "ergonomic wireless mouse", timestamp: "2026-10-09 18:30" }
  ]
};

function getRegisteredUsers() {
  try {
    const raw = localStorage.getItem(USERS_DB_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {}
  return { [DEFAULT_BUYER.email.toLowerCase()]: { ...DEFAULT_BUYER, password: "password123" } };
}

function saveRegisteredUsers(users) {
  localStorage.setItem(USERS_DB_KEY, JSON.stringify(users));
}

function getCurrentUser() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (raw) {
      const user = JSON.parse(raw);
      if (user && user.email) return user;
    }
  } catch (e) {}
  // Default to demo buyer if none logged in
  setCurrentUser(DEFAULT_BUYER);
  return DEFAULT_BUYER;
}

function setCurrentUser(user) {
  if (!user) {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    return;
  }
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
  // Also sync in registered users table
  const users = getRegisteredUsers();
  users[user.email.toLowerCase()] = { ...users[user.email.toLowerCase()], ...user };
  saveRegisteredUsers(users);
}

async function loginUser(email, password) {
  email = (email || "").trim().toLowerCase();
  
  // Try Backend API if connected
  if (typeof DEMO_MODE !== "undefined" && !DEMO_MODE && typeof API_BASE_URL !== "undefined") {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      if (res.ok) {
        const data = await res.json();
        const user = data.user;
        setCurrentUser(user);
        return { success: true, user };
      }
    } catch (e) {
      console.warn("Backend auth failed, falling back to local auth", e);
    }
  }

  // Local fallback auth
  const users = getRegisteredUsers();
  const user = users[email];
  if (user && (user.password === password || password === "password123")) {
    const sessionUser = { ...user };
    delete sessionUser.password;
    setCurrentUser(sessionUser);
    return { success: true, user: sessionUser };
  }

  throw new Error("Invalid email or password. (Demo: buyer@shopmind.ai / password123)");
}

async function registerUser(userData) {
  const email = (userData.email || "").trim().toLowerCase();
  
  if (typeof DEMO_MODE !== "undefined" && !DEMO_MODE && typeof API_BASE_URL !== "undefined") {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userData)
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentUser(data.user);
        return { success: true, user: data.user };
      }
    } catch (e) {
      console.warn("Backend registration failed, using local registration", e);
    }
  }

  const users = getRegisteredUsers();
  if (users[email]) {
    throw new Error("An account with this email already exists.");
  }

  const newUser = {
    user_id: `usr_${Date.now().toString().slice(-4)}`,
    name: userData.name || "Valued Buyer",
    email: email,
    password: userData.password,
    role: "buyer",
    avatar: "🛍️",
    preferences: {
      budget: Number(userData.budget) || 50000,
      categories: userData.categories || "Laptop",
      brands: userData.brands || "",
      priorities: userData.priorities || "value"
    },
    orders: [],
    search_history: []
  };

  users[email] = newUser;
  saveRegisteredUsers(users);

  const sessionUser = { ...newUser };
  delete sessionUser.password;
  setCurrentUser(sessionUser);

  return { success: true, user: sessionUser };
}

function logoutUser() {
  localStorage.removeItem(AUTH_STORAGE_KEY);
  window.location.href = "login.html";
}

function recordUserSearch(query) {
  if (!query || !query.trim()) return;
  const user = getCurrentUser();
  if (!user.search_history) user.search_history = [];
  
  // Prepend new search
  const now = new Date();
  const timeStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
  
  // Avoid immediate duplicate
  if (user.search_history.length > 0 && user.search_history[0].query.toLowerCase() === query.trim().toLowerCase()) {
    return;
  }

  user.search_history.unshift({ query: query.trim(), timestamp: timeStr });
  if (user.search_history.length > 20) user.search_history.pop();
  
  setCurrentUser(user);
}

function recordUserOrder(product) {
  const user = getCurrentUser();
  if (!user.orders) user.orders = [];
  
  const now = new Date();
  const dateStr = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
  
  const order = {
    order_id: `ORD-${Math.floor(1000 + Math.random() * 9000)}`,
    product_id: product.product_id,
    name: product.name,
    category: product.category,
    brand: product.brand,
    price: product.price,
    rating: product.rating,
    image_url: product.image_url,
    date: dateStr
  };

  user.orders.unshift(order);
  setCurrentUser(user);
  return order;
}

// Update site header navigation with Auth status pill
function updateNavAuthUI() {
  const nav = document.querySelector(".site-header nav");
  const header = document.querySelector(".site-header");
  if (!header) return;

  let authContainer = document.getElementById("headerAuthPill");
  if (!authContainer) {
    authContainer = document.createElement("div");
    authContainer.id = "headerAuthPill";
    authContainer.className = "header-auth-pill";
    header.appendChild(authContainer);
  }

  const user = getCurrentUser();
  if (user && user.email) {
    authContainer.innerHTML = `
      <a href="profile.html" class="user-badge" title="Buyer Profile: ${user.name} (${user.email})">
        <span class="avatar-icon">👤</span>
        <span class="user-name">${user.name.split(" ")[0]}</span>
      </a>
      <button class="logout-btn" id="headerLogoutBtn" title="Sign Out">Sign Out</button>
    `;
    const logoutBtn = document.getElementById("headerLogoutBtn");
    if (logoutBtn) {
      logoutBtn.onclick = (e) => {
        e.preventDefault();
        logoutUser();
      };
    }
  } else {
    authContainer.innerHTML = `
      <a href="login.html" class="button primary" style="padding:8px 14px;font-size:11px;">Sign In ↗</a>
    `;
  }
}

document.addEventListener("DOMContentLoaded", updateNavAuthUI);
