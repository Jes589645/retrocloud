import { useEffect, useState } from "react";
import { getGames, startSession } from "../api";

export default function Games() {
  const [games, setGames] = useState([]);
  const [sessionInfo, setSessionInfo] = useState(null);

  useEffect(() => {
    (async () => {
      const g = await getGames();
      setGames(g);
    })();
  }, []);

  const play = async (gameId) => {
    const session = await startSession(gameId);
    setSessionInfo(session);
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
      <h2>Juegos disponibles</h2>
      <ul>
        {games.map((g) => (
          <li key={g.id} style={{ marginBottom: 10 }}>
            {g.name}{" "}
            <button onClick={() => play(g.id)}>
              Jugar
            </button>
          </li>
        ))}
      </ul>

      {sessionInfo && (
        <div style={{ marginTop: 20 }}>
          <h3>Sesión creada</h3>
          <p>Session ID: {sessionInfo.session_id}</p>
          <p>VM Instance: {sessionInfo.vm_instance_id}</p>
          <p>
            Streaming URL (placeholder):{" "}
            <a href={sessionInfo.streaming_url}>{sessionInfo.streaming_url}</a>
          </p>
        </div>
      )}
    </div>
  );
}
