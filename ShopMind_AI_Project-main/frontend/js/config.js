// Auto-detect backend URL whether deployed on Render, custom host, or running locally
const API_BASE_URL = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? (window.location.port === "5500" ? "http://127.0.0.1:8002" : window.location.origin)
  : window.location.origin;

const DEMO_MODE = false;
