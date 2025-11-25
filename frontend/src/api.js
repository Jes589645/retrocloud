import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

let token = null;

export function setToken(t) {
  token = t;
}

function authHeaders() {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function login(username, password) {
  const data = new URLSearchParams();
  data.append("username", username);
  data.append("password", password);
  const res = await axios.post(`${API_BASE}/auth/login`, data);
  setToken(res.data.access_token);
  return res.data;
}

export async function register(username, password) {
  const res = await axios.post(`${API_BASE}/auth/register`, null, {
    params: { username, password },
  });
  return res.data;
}

export async function getGames() {
  const res = await axios.get(`${API_BASE}/games`, {
    headers: authHeaders(),
  });
  return res.data;
}

export async function startSession(gameId) {
  const res = await axios.post(
    `${API_BASE}/games/${gameId}/sessions`,
    {},
    { headers: authHeaders() }
  );
  return res.data;
}
