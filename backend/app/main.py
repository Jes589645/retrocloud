import os
import time
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

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
