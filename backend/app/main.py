from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from pydantic import BaseModel
from pathlib import Path
import json
import time
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
import json


from .orchestrator import GameOrchestrator


app = FastAPI(title="RetroCloud API")


# ============================================================
#                   GAME MODEL + CATALOG LOAD
# ============================================================

class Game(BaseModel):
    id: int
    name: str
    console: str
    filename: Optional[str] = None


# Ruta al JSON junto a main.py
CATALOG_PATH = Path(__file__).with_name("games_catalog.json")

GAMES: List[Game] = []

# Intentamos cargar el catálogo desde JSON, pero si no existe
# o está mal, dejamos la lista vacía (para no tumbar el backend).
if CATALOG_PATH.exists():
    try:
        with CATALOG_PATH.open("r", encoding="utf-8") as f:
            raw_games = json.load(f)
        GAMES = [Game(**g) for g in raw_games]
    except Exception as e:
        print(f"[WARN] No se pudo cargar games_catalog.json: {e}")
        GAMES = []
else:
    print(f"[INFO] games_catalog.json no encontrado en {CATALOG_PATH}, catálogo vacío.")


@app.get("/games", response_model=List[Game])
def list_games():
    return GAMES


@app.get("/debug/catalog")
def debug_catalog():
    return {
        "catalog_path": str(CATALOG_PATH),
        "exists": CATALOG_PATH.exists(),
        "count": len(GAMES),
        "sample": [g.dict() for g in GAMES[:5]],
    }


# ============================================================
#                   GAME ORCHESTRATION
# ============================================================

orchestrator = GameOrchestrator()


@app.post("/games/{game_id}/session")
def create_game_session(game_id: int):
    """
    Crea una instancia EC2 basada en la AMI retro gaming y devuelve su IP pública
    """
    game = next((g for g in GAMES if g.id == game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Juego no encontrado")

    instance_id, public_ip = orchestrator.launch_game_vm()

    return {
        "message": "Game VM creada correctamente",
        "instance_id": instance_id,
        "public_ip": public_ip,
        "connect_url": f"http://{public_ip}:3389",
        "game": game,
    }


# ============================================================
#                   SIMPLE HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": time.time()}


# ============================================================
#                   SIMPLE FRONTEND UI
# ============================================================

@app.get("/ui", response_class=HTMLResponse)
def ui():
    return """
    <html>
        <head>
            <title>RetroCloud</title>
            <style>
                body { font-family: Arial; padding: 20px; background: #111; color: #eee; }
                h1 { text-align: center; }
                .grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 20px;
                    padding-top: 20px;
                }
                .card {
                    background: #222;
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                    border: 1px solid #333;
                }
                button {
                    padding: 10px 15px;
                    background: #0f62fe;
                    border: none;
                    color: white;
                    border-radius: 5px;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <h1>🎮 RetroCloud</h1>
            <div id="games" class="grid"></div>

            <script>
                async function loadGames() {
                    const resp = await fetch("/games");
                    const games = await resp.json();

                    const container = document.getElementById("games");
                    container.innerHTML = "";

                    games.forEach(g => {
                        const card = document.createElement("div");
                        card.className = "card";
                        card.innerHTML = `
                            <h3>${g.name}</h3>
                            <p><b>Consola:</b> ${g.console}</p>
                            <button onclick="play(${g.id})">Jugar</button>
                        `;
                        container.appendChild(card);
                    });
                }

                async function play(id) {
                    alert("Creando VM de juego... espera 20-30s");

                    const resp = await fetch(`/games/${id}/session`, { method: "POST" });
                    const data = await resp.json();

                    alert("Tu VM está lista: " + data.public_ip);
                }

                loadGames();
            </script>
        </body>
    </html>
    """
