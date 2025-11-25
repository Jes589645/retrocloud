from datetime import timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import User, Game, GameSession, GameVM
from .auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from .orchestrator import get_or_create_vm, register_activity

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RetroCloud API")


# ======== AUTH =========

@app.post("/auth/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(username=username, hashed_password=get_password_hash(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username}


@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=60)
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ======== GAMES =========

@app.on_event("startup")
def seed_games():
    db = next(get_db())
    # Si ya hay juegos, no siembra
    if db.query(Game).count() > 0:
        return
    games = [
        Game(name="Super Mario World", slug="super-mario-world", max_sessions_per_vm=1),
        Game(name="Sonic the Hedgehog", slug="sonic-1", max_sessions_per_vm=1),
        Game(name="Street Fighter II", slug="sf2", max_sessions_per_vm=1),
        Game(name="Mega Man X", slug="mmx", max_sessions_per_vm=1),
    ]
    db.add_all(games)
    db.commit()


@app.get("/games")
def list_games(db: Session = Depends(get_db)):
    games = db.query(Game).all()
    return [{"id": g.id, "name": g.name, "slug": g.slug} for g in games]


# ======== GAME SESSIONS =========

@app.post("/games/{game_id}/sessions")
def start_session(
    game_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Obtener o crear VM
    vm = get_or_create_vm(db, max_sessions=game.max_sessions_per_vm)
    vm.current_sessions += 1
    register_activity(db, vm)
    db.commit()
    db.refresh(vm)

    # Aquí normalmente construirías la URL de streaming real (NICE DCV / etc.)
    streaming_url = f"https://placeholder-streaming/{vm.instance_id}/{game.slug}"

    session = GameSession(
        user_id=user.id,
        game_id=game.id,
        vm_id=vm.id,
        streaming_url=streaming_url,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "streaming_url": session.streaming_url,
        "vm_instance_id": vm.instance_id,
    }


@app.post("/sessions/{session_id}/end")
def end_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = (
        db.query(GameSession)
        .filter(GameSession.id == session_id, GameSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.ended_at = __import__("datetime").datetime.utcnow()

    vm = session.vm
    if vm.current_sessions > 0:
        vm.current_sessions -= 1
    register_activity(db, vm)
    db.commit()
    return {"detail": "Session ended"}
