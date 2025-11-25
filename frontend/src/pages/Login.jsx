import { useState } from "react";
import { login, register } from "../api";

export default function Login({ onLoggedIn }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("login");
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      if (mode === "login") {
        await login(username, password);
      } else {
        await register(username, password);
        await login(username, password);
      }
      onLoggedIn();
    } catch (err) {
      setError("Error al autenticar");
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "0 auto", padding: 20 }}>
      <h1>RetroCloud</h1>
      <h2>{mode === "login" ? "Iniciar sesión" : "Registrarse"}</h2>
      <form onSubmit={submit}>
        <input
          placeholder="Usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ display: "block", marginBottom: 10, width: "100%" }}
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ display: "block", marginBottom: 10, width: "100%" }}
        />
        <button type="submit" style={{ width: "100%", marginBottom: 10 }}>
          {mode === "login" ? "Entrar" : "Crear cuenta"}
        </button>
      </form>
      <button
        type="button"
        onClick={() => setMode(mode === "login" ? "register" : "login")}
        style={{ width: "100%" }}
      >
        {mode === "login"
          ? "¿No tienes cuenta? Regístrate"
          : "¿Ya tienes cuenta? Inicia sesión"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
