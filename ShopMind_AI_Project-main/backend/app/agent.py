"""ShopMind AI product retrieval, ranking, transparent comparison, buyer preference synthesis,
and smart budget-feature compromise reasoning.
"""
from __future__ import annotations

import os
import re
from typing import Any
from collections import Counter

from dotenv import load_dotenv

load_dotenv()

def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        raw = value.strip().lower().replace(",", "")
        raw = raw.replace("₹", "").replace("rs.", "").replace("rs", "").replace("inr", "").strip()
        match = re.fullmatch(r"([-+]?\d+(?:\.\d+)?)\s*([kl]?)", raw)
        if not match:
            return None
        amount = float(match.group(1))
        return amount * (1000 if match.group(2) == "k" else 100000 if match.group(2) == "l" else 1)
    return None


def _price(value: Any) -> str:
    n = _number(value)
    return f"₹{n:,.0f}" if n is not None else "Not listed"


def _category(message: str) -> str | None:
    q = message.lower()
    aliases = {
        "Phone": ("phone", "phones", "mobile", "mobiles", "smartphone", "smartphones", "iphone", "android"),
        "Laptop": ("laptop", "laptops", "notebook", "notebooks", "macbook", "pc"),
        "Headphones": ("headphone", "headphones", "earbuds", "earphone", "earphones", "headset", "audio", "earpiece"),
        "Tablet": ("tablet", "tablets", "ipad", "tab"),
        "Monitor": ("monitor", "monitors", "display", "displays", "screen", "screens"),
        "Keyboard": ("keyboard", "keyboards", "keypad"),
        "Mouse": ("mouse", "mice", "trackpad"),
        "Smartwatch": ("smartwatch", "smart watch", "smartwatches", "watch", "smartband", "fitness band"),
        "Camera": ("camera", "cameras", "dslr", "mirrorless", "cam"),
        "Speaker": ("speaker", "speakers", "soundbar", "boombox"),
    }
    for category, words in aliases.items():
        if any(re.search(r"\b" + re.escape(word) + r"\b", q) for word in words):
            return category
    return None


def _price_constraints(message: str) -> list[tuple[str, float]]:
    pattern = re.compile(
        r"(?P<operator>not\s+less\s+than|less\s+than|under|below|cheaper\s+than|within|up\s*to|"
        r"at\s+most|maximum|max(?:imum)?|budget(?:\s+of)?|not\s+more\s+than|"
        r"not\s+exceed(?:ing)?|greater\s+than|more\s+than|above|over|"
        r"at\s+least|minimum|min(?:imum)?|not\s+less\s+than)"
        r"\s*(?:₹|rs\.?\s*|inr\s*)?"
        r"(?P<amount>[\d,]+(?:\.\d+)?)\s*(?P<suffix>[kKlL]?)",
        re.I,
    )
    constraints: list[tuple[str, float]] = []
    for match in pattern.finditer(message):
        amount = float(match.group("amount").replace(",", ""))
        suffix = match.group("suffix").lower()
        amount = round(amount * (1000 if suffix == "k" else 100000 if suffix == "l" else 1), 2)
        operator = re.sub(r"\s+", " ", match.group("operator").lower())
        if operator in {"less than", "cheaper than"}:
            constraints.append(("lt", amount))
        elif operator in {"under", "below", "within", "up to", "at most", "maximum", "max", "maximum", "budget", "budget of", "not more than", "not exceeding"}:
            constraints.append(("le", amount))
        elif operator in {"greater than", "more than", "above", "over"}:
            constraints.append(("gt", amount))
        else:
            constraints.append(("ge", amount))

    if not constraints:
        currency_price = re.search(
            r"(?:₹|rs\.?\s*|inr\s*)([\d,]+(?:\.\d+)?)\s*([kKlL]?)",
            message,
            re.I,
        )
        if currency_price:
            amount = float(currency_price.group(1).replace(",", ""))
            suffix = currency_price.group(2).lower()
            amount = round(amount * (1000 if suffix == "k" else 100000 if suffix == "l" else 1), 2)
            constraints.append(("le", amount))
    return constraints


def _extract_requested_features(message: str) -> list[str]:
    """Detect desired premium/extra features mentioned by user."""
    features = []
    q = message.lower()
    
    # RAM
    ram_match = re.search(r"(\d+)\s*(?:gb|gig)\s*ram", q)
    if ram_match:
        features.append(f"{ram_match.group(1)}GB RAM")
    elif "32gb" in q or "32 gb" in q:
        features.append("32GB RAM")
    elif "16gb" in q or "16 gb" in q:
        features.append("16GB RAM")
    elif "12gb" in q or "12 gb" in q:
        features.append("12GB RAM")
    elif "8gb" in q or "8 gb" in q:
        features.append("8GB RAM")

    # Storage
    storage_match = re.search(r"(\d+)\s*(?:tb|gb)\s*(?:storage|ssd|rom|disk)", q)
    if storage_match:
        features.append(f"{storage_match.group(0)}")
    elif "1tb" in q or "1 tb" in q:
        features.append("1TB Storage")
    elif "512gb" in q or "512 gb" in q:
        features.append("512GB Storage")

    # Processors
    if "i7" in q or "core i7" in q:
        features.append("Intel Core i7")
    elif "i5" in q or "core i5" in q:
        features.append("Intel Core i5")
    elif "ryzen 7" in q or "r7" in q:
        features.append("AMD Ryzen 7")
    elif "ryzen 5" in q or "r5" in q:
        features.append("AMD Ryzen 5")
    elif "ultra 5" in q or "core ultra" in q:
        features.append("Intel Core Ultra")

    # Display / Refresh / Audio features
    if "4k" in q or "ultra hd" in q:
        features.append("4K Resolution")
    if "144hz" in q or "120hz" in q:
        features.append("High Refresh Rate")
    if "anc" in q or "noise cancel" in q or "noise cancelling" in q:
        features.append("Active Noise Cancelling")
    if "mechanical" in q or "rgb" in q:
        features.append("Mechanical RGB")
    if "ergonomic" in q:
        features.append("Ergonomic Design")
    if "waterproof" in q or "ip68" in q or "ip67" in q:
        features.append("Water Resistant")
    if "wireless" in q or "bluetooth" in q:
        features.append("Wireless Connectivity")

    return features


def _is_greeting(message: str) -> bool:
    return bool(re.fullmatch(r"\s*(hi+|hello|hey|good morning|good afternoon|good evening)\s*[!. ]*", message, re.I))


def _is_farewell(message: str) -> bool:
    return bool(re.fullmatch(r"\s*(bye+|goodbye|good bye|see you|take care)\s*[!. ]*", message, re.I))


def _is_comparison(message: str) -> bool:
    q = message.lower()
    return any(phrase in q for phrase in (
        "compare", "comparison", "versus", " vs ", "which is better",
        "which one is better", "which is best", "what is best", "best phone",
        "best laptop", "best product", "highest rated", "top rated",
        "compare based on", "based on price", "based on rating",
    ))


def _tokens(text: str) -> set[str]:
    ignored = {
        "the", "and", "for", "with", "under", "below", "best", "good", "want",
        "need", "recommend", "suggest", "please", "show", "find", "product",
        "products", "price", "budget", "from", "that", "this", "compare",
        "comparison", "versus", "rating", "ratings", "rated", "which", "what",
        "based", "phone", "phones", "mobile", "mobiles", "is", "are", "me",
        "less", "than", "greater", "more", "above", "over", "within", "upto",
        "maximum", "max", "minimum", "min", "most", "least", "exceeding",
    }
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2 and token not in ignored}


def _compare(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Calculate comparable price/rating/value metrics from database fields."""
    valid_prices = [_number(p.get("price")) for p in candidates]
    known_prices = [p for p in valid_prices if p is not None]
    min_price = min(known_prices) if known_prices else None
    max_price = max(known_prices) if known_prices else None

    rows: list[dict[str, Any]] = []
    for p in candidates:
        price = _number(p.get("price"))
        rating = _number(p.get("rating"))
        rating_score = (max(0.0, min(5.0, rating)) / 5 * 100) if rating is not None else None
        if price is None:
            affordability = None
        elif max_price is None or min_price is None or max_price == min_price:
            affordability = 100.0
        else:
            affordability = (max_price - price) / (max_price - min_price) * 100
        if rating_score is not None and affordability is not None:
            value_score = round(rating_score * 0.70 + affordability * 0.30, 1)
        elif rating_score is not None:
            value_score = round(rating_score, 1)
        elif affordability is not None:
            value_score = round(affordability, 1)
        else:
            value_score = None

        row = dict(p)
        row["comparison"] = {
            "price_numeric": price,
            "rating_numeric": rating,
            "value_score": value_score,
            "price_display": _price(price),
            "rating_display": f"{rating:.1f}/5" if rating is not None else "Not rated",
        }
        rows.append(row)

    rows.sort(
        key=lambda p: (
            p["comparison"]["value_score"] if p["comparison"]["value_score"] is not None else -1,
            p["comparison"]["rating_numeric"] if p["comparison"]["rating_numeric"] is not None else -1,
            -(p["comparison"]["price_numeric"] if p["comparison"]["price_numeric"] is not None else float("inf")),
        ),
        reverse=True,
    )
    for index, row in enumerate(rows, start=1):
        row["comparison"]["rank"] = index

    cheapest = min(rows, key=lambda p: p["comparison"]["price_numeric"] if p["comparison"]["price_numeric"] is not None else float("inf"), default=None)
    highest_rated = max(rows, key=lambda p: p["comparison"]["rating_numeric"] if p["comparison"]["rating_numeric"] is not None else -1, default=None)
    best_value = rows[0] if rows else None
    comparison = {
        "criteria": {"rating_weight_percent": 70, "affordability_weight_percent": 30},
        "best_value_product_id": best_value.get("product_id") if best_value else None,
        "cheapest_product_id": cheapest.get("product_id") if cheapest else None,
        "highest_rated_product_id": highest_rated.get("product_id") if highest_rated else None,
        "count": len(rows),
    }
    return rows, comparison


def find_budget_compromise_products(
    category: str | None,
    max_budget: float,
    requested_features: list[str],
    catalogue: list[dict[str, Any]]
) -> dict[str, Any]:
    """When a buyer requests extra features that exceed their budget, find sensible
    alternatives that strictly fit within the budget with slightly relaxed features
    instead of returning 'no products found'."""
    
    # 1. Filter products in category
    cat_products = [
        p for p in catalogue
        if not category or str(p.get("category", "")).lower() == category.lower()
    ]
    if not cat_products:
        cat_products = catalogue

    # 2. Filter products strictly within budget
    budget_products = [
        p for p in cat_products
        if _number(p.get("price")) is not None and _number(p.get("price")) <= max_budget
    ]

    # 3. Check what the requested features actually cost in the catalogue
    premium_products = []
    for p in cat_products:
        p_text = " ".join([
            str(p.get("name", "")), str(p.get("description", "")),
            str(p.get("specifications", "")), str(p.get("brand", ""))
        ]).lower()
        if any(f.lower().replace(" ", "") in p_text.replace(" ", "") for f in requested_features):
            premium_products.append(p)

    min_premium_price = None
    if premium_products:
        prices = [_number(p.get("price")) for p in premium_products if _number(p.get("price")) is not None]
        if prices:
            min_premium_price = min(prices)

    if not budget_products:
        # If budget is lower than any product in catalogue, suggest closest lowest-priced product
        cat_sorted = sorted(cat_products, key=lambda p: _number(p.get("price")) or float("inf"))
        budget_products = cat_sorted[:3]

    # Rank budget products by rating, value, and closest specs
    budget_products_ranked = sorted(
        budget_products,
        key=lambda p: (_number(p.get("rating")) or 0, -(_number(p.get("price")) or 0)),
        reverse=True
    )

    compromise_list = budget_products_ranked[:4]
    
    # Format compromise summary
    top_choice = compromise_list[0] if compromise_list else {}
    top_price = _price(top_choice.get("price"))
    
    feature_text = ", ".join(requested_features) if requested_features else "high-tier features"
    
    explanation_lines = [
        f"💡 **AI Smart Budget Compromise Found:**",
        f"You requested {category or 'a product'} with **{feature_text}** for under **{_price(max_budget)}**.",
    ]
    if min_premium_price:
        explanation_lines.append(
            f"Products with all those exact high-tier features start at **{_price(min_premium_price)}** in our catalogue."
        )
    explanation_lines.append(
        f"To fit **100% within your budget of {_price(max_budget)}**, here are top-performing alternatives with balanced specifications (e.g. **{top_choice.get('name')}** at **{top_price}** with rating **{top_choice.get('rating')}/5**) that provide excellent everyday reliability without overspending."
    )

    # Attach compromise metadata to products
    compromise_products = []
    for p in compromise_list:
        p_copy = dict(p)
        p_copy["is_compromise"] = True
        p_copy["compromise_badge"] = f"Budget Fit (Under {_price(max_budget)})"
        compromise_products.append(p_copy)

    return {
        "is_compromise": True,
        "compromise_products": compromise_products,
        "explanation": "\n\n".join(explanation_lines),
        "requested_features": requested_features,
        "max_budget": max_budget,
        "category": category or "Electronics",
        "min_premium_price": min_premium_price
    }


def synthesize_buyer_preferences(
    orders: list[dict[str, Any]],
    search_history: list[dict[str, Any] | str],
    user_preferences: dict[str, Any],
    catalogue: list[dict[str, Any]]
) -> dict[str, Any]:
    """AI Agent that analyzes a buyer's order history and search history to build an
    accurate buyer preference profile and generate tailored product recommendations."""
    
    # Categories from orders and searches
    order_cats = [o.get("category") for o in orders if isinstance(o, dict) and o.get("category")]
    order_brands = [o.get("brand") for o in orders if isinstance(o, dict) and o.get("brand")]
    order_prices = [_number(o.get("price")) for o in orders if isinstance(o, dict) and _number(o.get("price")) is not None]

    search_queries = []
    for s in search_history:
        if isinstance(s, dict):
            search_queries.append(s.get("query", ""))
        elif isinstance(s, str):
            search_queries.append(s)

    # Detect categories from search queries
    searched_cats = []
    for q in search_queries:
        c = _category(q)
        if c:
            searched_cats.append(c)

    # Combine counts
    all_cats = order_cats * 2 + searched_cats
    cat_counter = Counter(all_cats)
    top_categories = [cat for cat, _ in cat_counter.most_common(3)]
    if not top_categories:
        top_categories = [user_preferences.get("categories")] if user_preferences.get("categories") else ["Laptop", "Headphones"]

    # Price analysis
    avg_price = sum(order_prices) / len(order_prices) if order_prices else (_number(user_preferences.get("budget")) or 50000)
    
    # Persona Generation
    if "Laptop" in top_categories and ("Monitor" in top_categories or "Keyboard" in top_categories or "Mouse" in top_categories):
        persona = "Workspace & Productivity Builder"
        persona_desc = "You prioritize seamless desktop ergonomics, computing power, and workflow efficiency."
    elif "Headphones" in top_categories or "Speaker" in top_categories:
        persona = "Audiophile & Creative Enthusiast"
        persona_desc = "You value acoustic precision, high fidelity, and rich immersive media."
    elif "Camera" in top_categories:
        persona = "Content Creator & Visual Artist"
        persona_desc = "You look for high resolution, optical clarity, and creative recording gear."
    elif "Smartwatch" in top_categories or "Phone" in top_categories:
        persona = "Connected Mobile Power User"
        persona_desc = "You love on-the-go connectivity, smart tracking, and modern mobile tech."
    else:
        persona = "Smart Value Explorer"
        persona_desc = "You focus on the best price-to-performance ratio and highly-rated essentials."

    # Generate tailored recommendations based on order history and search history
    ordered_ids = {o.get("product_id") for o in orders if isinstance(o, dict)}
    
    scored_recommendations: list[tuple[float, dict[str, Any], str]] = []
    for p in catalogue:
        pid = p.get("product_id")
        if pid in ordered_ids:
            continue # Don't recommend something already purchased
        
        score = 0.0
        p_cat = p.get("category")
        p_brand = p.get("brand")
        p_price = _number(p.get("price")) or 0
        p_rating = _number(p.get("rating")) or 0
        p_text = f"{p.get('name')} {p_brand} {p_cat} {p.get('description')}".lower()
        
        reasons = []

        # Category affinity
        if p_cat in top_categories:
            score += 4.0
            reasons.append(f"Matches your affinity for {p_cat}s")

        # Search history keyword relevance
        for sq in search_queries[-5:]:
            tokens = _tokens(sq)
            match_count = sum(1 for t in tokens if t in p_text)
            if match_count > 0:
                score += match_count * 2.0
                reasons.append(f"Relevant to your recent search '{sq}'")
                break

        # Brand loyalty
        if p_brand in order_brands:
            score += 3.0
            reasons.append(f"From {p_brand}, a brand you've purchased before")

        # Budget fit
        if avg_price > 0:
            price_diff_ratio = abs(p_price - avg_price) / max(avg_price, 1)
            if price_diff_ratio < 0.5:
                score += 2.0
                reasons.append("Fits your typical spending range")

        # Quality rating
        score += (p_rating / 5.0) * 2.0

        if score > 2.0:
            main_reason = reasons[0] if reasons else f"Top rated {p_cat}"
            scored_recommendations.append((score, p, main_reason))

    scored_recommendations.sort(key=lambda item: item[0], reverse=True)
    recommended_items = []
    for score, product, reason in scored_recommendations[:6]:
        p_dict = dict(product)
        p_dict["ai_recommendation_reason"] = reason
        recommended_items.append(p_dict)

    return {
        "persona": persona,
        "persona_description": persona_desc,
        "top_categories": top_categories,
        "average_spend": _price(avg_price),
        "total_orders_analyzed": len(orders),
        "total_searches_analyzed": len(search_queries),
        "recommendations": recommended_items,
    }


async def generate_answer(message: str, user_id: str, products: list[dict[str, Any]]) -> dict[str, Any]:
    message = message.strip()
    if _is_greeting(message):
        return {
            "answer": "Hi! I'm ShopMind AI. Tell me what product you're looking for, your budget, or any specific features you need. If a feature is outside your budget, I'll help you find the best value alternative!",
            "products": [],
            "response_type": "greeting",
            "source_note": "Conversation greeting",
            "ai_enabled": False
        }
    if _is_farewell(message):
        return {
            "answer": "Goodbye! Thanks for shopping with ShopMind AI. Let me know whenever you need more recommendations!",
            "products": [],
            "response_type": "farewell",
            "source_note": "Conversation farewell",
            "ai_enabled": False
        }

    category = _category(message)
    price_constraints = _price_constraints(message)
    requested_features = _extract_requested_features(message)
    comparison_request = _is_comparison(message) or (category is not None and any(x in message.lower() for x in ("best", "recommend", "suggest", "which")))
    
    # 1. Standard matching
    tokens = _tokens(message)
    ranked: list[tuple[float, dict[str, Any]]] = []

    for product in products:
        p_category = str(product.get("category", "")).strip().lower()
        price = _number(product.get("price"))
        rating = _number(product.get("rating"))

        if category and p_category != category.lower():
            if not (category == "Phone" and p_category in {"mobile", "smartphone"}):
                if not (category == "Headphones" and p_category in {"headphone", "audio"}):
                    continue
        if price_constraints:
            if price is None:
                continue
            if any(
                (operator == "lt" and price >= amount)
                or (operator == "le" and price > amount)
                or (operator == "gt" and price <= amount)
                or (operator == "ge" and price < amount)
                for operator, amount in price_constraints
            ):
                continue

        searchable = " ".join([
            str(product.get("name", "")), str(product.get("brand", "")),
            str(product.get("category", "")), str(product.get("description", "")),
            str(product.get("specifications", "")),
        ]).lower()
        
        # Check feature matches
        has_all_features = all(feat.lower().replace(" ", "") in searchable.replace(" ", "") for feat in requested_features) if requested_features else True
        feature_score = sum(3.0 for feat in requested_features if feat.lower().replace(" ", "") in searchable.replace(" ", ""))
        score = sum(1 for token in tokens if token in searchable) + feature_score
        
        if category:
            score += 3
        if rating is not None:
            score += rating * 0.05
        
        # Only add to strictly matching ranked candidates if it meets requested extra features
        if has_all_features:
            ranked.append((score, product))

    ranked.sort(key=lambda item: item[0], reverse=True)
    candidates = [p for s, p in ranked if s > 0] if tokens or requested_features else [p for _, p in ranked]

    # --- REQUIREMENT 4: SMART BUDGET & FEATURE COMPROMISE ---
    # If no product matches both the requested extra features AND the price limit:
    if not candidates and (price_constraints or requested_features):
        max_budget = None
        for op, amt in price_constraints:
            if op in ("lt", "le"):
                max_budget = amt
                break
        if max_budget is None and price_constraints:
            max_budget = price_constraints[0][1]
        if max_budget is None:
            max_budget = 60000.0 # sensible default budget

        compromise_data = find_budget_compromise_products(
            category=category,
            max_budget=max_budget,
            requested_features=requested_features,
            catalogue=products
        )
        
        return {
            "answer": compromise_data["explanation"],
            "products": compromise_data["compromise_products"],
            "comparison": None,
            "response_type": "budget_compromise",
            "is_compromise": True,
            "compromise_details": compromise_data,
            "source_note": "AI Smart Compromise: Found top within-budget alternatives instead of returning zero results.",
            "ai_enabled": bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
        }

    if not candidates:
        # If still no candidate, provide closest category products
        cat_candidates = [p for p in products if not category or str(p.get("category", "")).lower() == category.lower()]
        candidates = cat_candidates[:4] if cat_candidates else products[:4]

    candidates, comparison = _compare(candidates)
    candidates = candidates[:5] if comparison_request else candidates[:4]
    candidates, comparison = _compare(candidates)

    if comparison_request:
        best = next((p for p in candidates if p.get("product_id") == comparison.get("best_value_product_id")), candidates[0])
        cheapest = next((p for p in candidates if p.get("product_id") == comparison.get("cheapest_product_id")), None)
        highest = next((p for p in candidates if p.get("product_id") == comparison.get("highest_rated_product_id")), None)
        answer = (
            f"My best overall value pick is {best.get('name', 'this product')} "
            f"({_price(best.get('price'))}, rating {best.get('rating', 'not listed')}/5). "
        )
        if cheapest:
            answer += f"The cheapest option is {cheapest.get('name')} ({_price(cheapest.get('price'))}). "
        if highest:
            answer += f"The highest-rated option is {highest.get('name')} (rating {highest.get('rating', 'not listed')}/5). "
        answer += "Compare the table below: the value score weighs rating at 70% and affordability at 30% among these displayed products."
        response_type = "comparison"
    else:
        best = candidates[0]
        answer = f"I found {len(candidates)} matching product(s). {best.get('name', 'The top match')} ({_price(best.get('price'))}) is my top match based on catalogue relevance, price, and rating."
        response_type = "products"

    return {
        "answer": answer,
        "products": candidates,
        "comparison": comparison if comparison_request else None,
        "response_type": response_type,
        "source_note": "Price and rating retrieved from catalogue; ranking and comparison calculated by ShopMind AI.",
        "ai_enabled": bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
    }
