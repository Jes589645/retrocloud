import os
import time
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from pydantic import BaseModel

from .orchestrator import GameOrchestrator

# Cargar variables de entorno desde backend/.env
load_dotenv()

app = FastAPI(title="RetroCloud API")

# ----- Modelos Pydantic -----


class Game(BaseModel):
    id: int
    name: str
    console: str


class GameSession(BaseModel):
    session_id: int
    game_id: int
    instance_id: str
    public_ip: str
    state: str


# Catálogo estático por ahora (todo SNES, como definiste el proyecto)
GAMES: List[Game] = [
    Game(id=1, name="Super Mario World", console="SNES"),
    Game(id=2, name="The Legend of Zelda: A Link to the Past", console="SNES"),
    Game(id=3, name="Donkey Kong Country", console="SNES"),
]

# ----- Orquestador EC2 -----

GAME_AMI_ID = os.getenv("GAME_AMI_ID")
GAME_AWS_REGION = os.getenv("GAME_AWS_REGION", "us-east-2")
GAME_INSTANCE_TYPE = os.getenv("GAME_INSTANCE_TYPE", "m7i-flex.large")

orchestrator = GameOrchestrator(
    ami_id=GAME_AMI_ID,
    region_name=GAME_AWS_REGION,
    instance_type=GAME_INSTANCE_TYPE,
)


@app.get("/")
def root():
    return {"message": "RetroCloud backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/games", response_model=List[Game])
def list_games():
    return GAMES


@app.post("/games/{game_id}/sessions", response_model=GameSession)
def create_game_session(game_id: int):
    # Buscar el juego
    game = next((g for g in GAMES if g.id == game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Por ahora, user_id fijo (luego lo sacaremos del token JWT)
    user_id = 1

    vm_info = orchestrator.create_game_vm(user_id=user_id, game_id=game_id)

    return GameSession(
        session_id=int(time.time()),  # placeholder
        game_id=game_id,
        instance_id=vm_info["instance_id"],
        public_ip=vm_info["public_ip"],
        state=vm_info["state"],
    )

@app.get("/test-deploy")
def test_deploy():
    return {"status": "deployment OK"}

@app.get("/ui", response_class=HTMLResponse)
def ui():
    return """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>RetroCloud – Catálogo de juegos</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #e5e7eb;
      margin: 0;
      padding: 0;
    }
    header {
      padding: 1.5rem 2rem;
      background: #020617;
      border-bottom: 1px solid #1f2937;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    header h1 {
      margin: 0;
      font-size: 1.4rem;
    }
    header span {
      font-size: 0.85rem;
      color: #9ca3af;
    }
    main {
      max-width: 960px;
      margin: 1.5rem auto;
      padding: 0 1rem 2rem;
    }
    #status {
      margin-bottom: 1rem;
      padding: 0.75rem 1rem;
      border-radius: 0.5rem;
      font-size: 0.9rem;
      background: #020617;
      border: 1px solid #1f2937;
      display: none;
    }
    #status.ok {
      border-color: #22c55e;
      color: #bbf7d0;
    }
    #status.error {
      border-color: #ef4444;
      color: #fecaca;
    }
    .games-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin-top: 1rem;
    }
    .game-card {
      background: #020617;
      border-radius: 0.75rem;
      border: 1px solid #111827;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      box-shadow: 0 10px 25px rgba(0,0,0,0.45);
    }
    .game-title {
      font-size: 1rem;
      font-weight: 600;
    }
    .game-console {
      font-size: 0.85rem;
      color: #9ca3af;
    }
    .game-footer {
      margin-top: 0.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.5rem;
    }
    button {
      border: none;
      border-radius: 999px;
      padding: 0.4rem 0.9rem;
      font-size: 0.85rem;
      cursor: pointer;
      background: #22c55e;
      color: #022c22;
      font-weight: 600;
      transition: transform 0.06s ease, box-shadow 0.06s ease, background 0.1s ease;
      box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
    }
    button:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(34, 197, 94, 0.5);
    }
    button:disabled {
      background: #4b5563;
      color: #9ca3af;
      box-shadow: none;
      cursor: default;
      transform: none;
    }
    .session-info {
      font-size: 0.78rem;
      color: #9ca3af;
      margin-top: 0.35rem;
      word-break: break-all;
    }
    .session-info strong {
      color: #e5e7eb;
    }
    .small-label {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #6b7280;
    }
    .pill {
      padding: 0.1rem 0.5rem;
      border-radius: 999px;
      border: 1px solid #1f2937;
      font-size: 0.75rem;
      color: #9ca3af;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>RetroCloud</h1>
      <span>Prueba de concepto · Cloud gaming retro 2D</span>
    </div>
    <div class="pill">Backend FastAPI · AWS EC2</div>
  </header>

  <main>
    <div id="status"></div>

    <section>
      <div class="small-label">Catálogo</div>
      <h2 style="margin: 0.15rem 0 0.5rem; font-size: 1.1rem;">Juegos disponibles</h2>
      <p style="font-size: 0.85rem; color: #9ca3af; margin-top: 0;">
        Selecciona un juego para lanzar una nueva máquina de juego basada en la AMI retro.
      </p>
      <div id="games" class="games-grid"></div>
    </section>
  </main>

  <script>
    const API_BASE = "";

    const statusBox = document.getElementById("status");
    const gamesContainer = document.getElementById("games");

    function setStatus(message, type = "ok") {
      statusBox.textContent = message;
      statusBox.className = "";
      statusBox.classList.add(type === "ok" ? "ok" : "error");
      statusBox.style.display = "block";
    }

    async function loadGames() {
      try {
        const resp = await fetch(API_BASE + "/games");
        if (!resp.ok) {
          throw new Error("Error al cargar juegos: " + resp.status);
        }
        const games = await resp.json();
        renderGames(games);
      } catch (err) {
        console.error(err);
        setStatus("No se pudieron cargar los juegos. Revisa el backend.", "error");
      }
    }

    function renderGames(games) {
      gamesContainer.innerHTML = "";
      if (!games || games.length === 0) {
        gamesContainer.innerHTML = "<p>No hay juegos configurados.</p>";
        return;
      }

      for (const game of games) {
        const card = document.createElement("div");
        card.className = "game-card";
        card.innerHTML = `
          <div class="game-title">${game.name}</div>
          <div class="game-console">${game.console}</div>
          <div class="game-footer">
            <button data-game-id="${game.id}">Jugar</button>
          </div>
          <div class="session-info" id="session-info-${game.id}" style="display:none;"></div>
        `;

        const button = card.querySelector("button");
        const sessionInfo = card.querySelector(".session-info");

        button.addEventListener("click", async () => {
          const gameId = button.getAttribute("data-game-id");
          button.disabled = true;
          button.textContent = "Creando sesión...";

          sessionInfo.style.display = "none";
          sessionInfo.textContent = "";

          try {
            const resp = await fetch(API_BASE + `/games/${gameId}/sessions`, {
              method: "POST"
            });

            if (!resp.ok) {
              throw new Error("Error HTTP " + resp.status);
            }

            const data = await resp.json();

            const streaming = data.streaming_url || `rdp://${data.public_ip}:3389`;

            sessionInfo.innerHTML = `
              <strong>Sesión creada</strong><br/>
              Instancia: ${data.instance_id}<br/>
              IP: ${data.public_ip}<br/>
              URL de conexión: ${streaming}
            `;
            sessionInfo.style.display = "block";

            setStatus("Sesión creada correctamente para \"" + game.name + "\"", "ok");
          } catch (err) {
            console.error(err);
            setStatus("No se pudo crear la sesión para \"" + game.name + "\"", "error");
          } finally {
            button.disabled = false;
            button.textContent = "Jugar";
          }
        });

        gamesContainer.appendChild(card);
      }
    }

    loadGames();
  </script>
</body>
</html>
    """
