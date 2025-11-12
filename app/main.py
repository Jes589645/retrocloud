import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from auth import valid_password, hash_password, verify_password
import ddb

load_dotenv()
app = FastAPI(title="retrocloud")
DCV_HOST = os.getenv("DCV_HOSTNAME")
DCV_PORT = os.getenv("DCV_PORT","8443")

class Credentials(BaseModel):
    username: str
    password: str

@app.post("/signup")
def signup(c: Credentials):
    if not valid_password(c.password):
        raise HTTPException(400, "La contraseña no cumple la política.")
    if ddb.get_user(c.username):
        raise HTTPException(409, "Usuario ya existe.")
    ddb.create_user(c.username, hash_password(c.password))
    return {"ok": True}

@app.post("/login")
def login(c: Credentials):
    u = ddb.get_user(c.username)
    if not u or not verify_password(c.password, u["password_hash"]):
        raise HTTPException(401, "Credenciales inválidas.")
    s = ddb.upsert_session(c.username)
    if s is None:
        raise HTTPException(409, "Ya tienes una sesión activa.")
    return {"ok": True, "session_id": s["session_id"]}

@app.post("/logout")
def logout(c: Credentials):
    u = ddb.get_user(c.username)
    if not u or not verify_password(c.password, u["password_hash"]):
        raise HTTPException(401, "Credenciales inválidas.")
    ddb.end_session(c.username)
    return {"ok": True}

@app.get("/play")
def play(username: str):
    # refresca TTL (simulamos actividad)
    if not ddb.get_user(username):
        raise HTTPException(404, "Usuario no existe.")
    ddb.touch_session(username)
    # Redirige al cliente web de DCV en la instancia
    return RedirectResponse(url=f"https://{DCV_HOST}:{DCV_PORT}/")
