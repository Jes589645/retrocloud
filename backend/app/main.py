from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
import json
import time
import os

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
        print(f"[INFO] Catálogo cargado: {len(GAMES)} juegos.")
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

# Leemos el GAME_AMI_ID desde las variables de entorno
GAME_AMI_ID = os.getenv("GAME_AMI_ID")
if not GAME_AMI_ID:
    # En la EC2 esto viene de systemd (Environment="GAME_AMI_ID=...")
    # En local, si no está, se lanza un error claro.
    raise ValueError("GAME_AMI_ID no está configurado en el entorno")

# Instanciamos el orquestador con la AMI de juegos
orchestrator = GameOrchestrator(GAME_AMI_ID)


@app.post("/games/{game_id}/session")
def create_game_session(game_id: int):
    """
    Crea una instancia EC2 basada en la AMI retro gaming y devuelve su IP pública.
    Además, le pasa al orquestador el nombre de la ROM y la consola.
    """
    game = next((g for g in GAMES if g.id == game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Juego no encontrado")

    if not game.filename:
        raise HTTPException(
            status_code=500,
            detail="Juego sin filename definido en el catálogo",
        )

    instance_id, public_ip = orchestrator.launch_game_vm(
        rom_filename=game.filename,
        console=game.console,
    )

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
            <h1>RetroCloud</h1>
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

                    if (data.public_ip) {
                        alert("Tu VM está lista en: " + data.public_ip + "\\nConéctate por RDP al puerto 3389.");
                    } else if (data.detail) {
                        alert("Error: " + data.detail);
                    } else {
                        alert("Se creó la sesión, pero no se obtuvo IP pública todavía.");
                    }
                }

                loadGames();
            </script>
        </body>
    </html>
    """
