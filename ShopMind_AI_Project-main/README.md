<img width="1861" height="888" alt="Screenshot 2026-10-11 124901" src="https://github.com/user-attachments/assets/fb3fb984-8912-4327-a3c9-9a5fe1818560" />
# ShopMind AI — HTML/CSS/JS + FastAPI + MongoDB + LangGraph

## AI features implemented
- LangGraph workflow: catalogue retrieval/ranking node → grounded answer node.
- MongoDB remains the source of truth for product names, prices, ratings, descriptions and specifications.
- Category/budget filtering and relevance ranking.
- OpenRouter LLM integration via `langchain-openai` for natural-language explanations.
- Fallback mode if no API key is configured or the remote model is unavailable.
- FastAPI `/api/chat` returns the explanation and separate product cards.

This starter retrieves structured product data directly from MongoDB; it does not yet use a vector database. Add embeddings/vector search later for long manuals and reviews, while keeping prices/specifications grounded in MongoDB. Mem0 preference memory is not enabled in this version.

## 1. Backend setup (Windows)
From `shopmind_ai_project\backend`:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```
Edit `.env`, set your `OPENROUTER_API_KEY`, and ensure MongoDB is running. Leave the key blank to test catalogue retrieval only. Keep the key in backend `.env`, never frontend JavaScript.

Then seed sample catalogue data and start the API:
```powershell
python seed_products.py
uvicorn app.main:app --reload --port 8000
```
API docs: http://127.0.0.1:8000/docs

## 2. Frontend setup
From project root, in a second terminal:
```powershell
python -m http.server 5500 --directory frontend
```
Open `http://localhost:5500/html/products.html` to browse the full 100-product illustrative sample catalogue (including all categories) in demo mode. The same sample catalogue is available to the demo chat and compare pages. Set `DEMO_MODE = false` in `frontend/js/config.js` so the pages call FastAPI for MongoDB-backed products.

## 3. Test prompts
- `Recommend a laptop under ₹65000 for programming`
- `I need headphones for studying under ₹10000`
- `Suggest a phone under ₹40000`

Sample products are illustrative demo data, not real inventory. Replace them with verified catalogue data.

## Request flow
`chat.html → frontend/js/api.js → FastAPI /api/chat → MongoDB → LangGraph retrieval/ranking → OpenRouter LLM grounded in retrieved records → answer + product cards`
