import { useState, useEffect } from 'react';

// URL de la API: En desarrollo usa localhost, en prod usa la IP del servidor (inyectada por Vite)
// Si VITE_API_URL no está definida, intenta inferirla o usa localhost como fallback
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Catálogo Hardcodeado para el PoC (Ya que no tenemos el JSON generado en la VM Linux aún)
// Mismos nombres exactos que tus ROMs en la AMI
const GAMES = [
  { id: 'SuperMarioWorld.smc', name: 'Super Mario World', img: 'https://upload.wikimedia.org/wikipedia/en/3/32/Super_Mario_World_Coverart.png' },
  { id: 'DonkeyKongCountry.sfc', name: 'Donkey Kong Country', img: 'https://upload.wikimedia.org/wikipedia/en/c/c1/Donkey_Kong_Country_SNES_cover.png' },
  { id: 'ZeldaALinkToThePast.sfc', name: 'Zelda: A Link to the Past', img: 'https://upload.wikimedia.org/wikipedia/en/2/21/The_Legend_of_Zelda_A_Link_to_the_Past_SNES_Game_Cover.jpg' }
];

export default function App() {
  const [activeSession, setActiveSession] = useState(null);
  const [loading, setLoading] = useState(false);

  const startGame = async (gameId) => {
    setLoading(true);
    try {
      console.log("Conectando a API:", API_URL);
      const res = await fetch(`${API_URL}/games/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_filename: gameId })
      });
      
      if (!res.ok) {
        const err = await res.text();
        throw new Error(err);
      }

      const data = await res.json();
      setActiveSession(data);
    } catch (error) {
      alert('Error lanzando el juego: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const stopGame = async () => {
    if (!activeSession) return;
    if(!confirm("¿Seguro que quieres apagar la máquina?")) return;
    
    try {
      await fetch(`${API_URL}/sessions/${activeSession.instance_id}`, { method: 'DELETE' });
      setActiveSession(null);
    } catch (e) {
      alert("Error al detener: " + e);
    }
  };

  return (
    <div style={{ background: '#1a1a1a', color: 'white', minHeight: '100vh', padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1 style={{ textAlign: 'center', color: '#a855f7', marginBottom: '2rem' }}>☁️ RetroCloud PoC</h1>
      
      {activeSession ? (
        <div style={{ maxWidth: '600px', margin: '0 auto', background: '#333', padding: '2rem', borderRadius: '10px' }}>
          <h2 style={{ color: '#4ade80' }}>🚀 Servidor Listo</h2>
          <div style={{ background: 'black', padding: '1rem', margin: '1rem 0' }}>
            <strong>URL:</strong> <a href={activeSession.url} target="_blank" style={{ color: '#60a5fa' }}>{activeSession.url}</a><br/>
            <strong>User:</strong> {activeSession.user}<br/>
            <strong>Pass:</strong> {activeSession.pass}
          </div>
          <button onClick={stopGame} style={{ background: '#ef4444', color: 'white', border: 'none', padding: '10px', width: '100%', cursor: 'pointer' }}>🛑 Apagar</button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem' }}>
          {GAMES.map(g => (
            <div key={g.id} style={{ background: '#2d2d2d', borderRadius: '10px', padding: '1rem', textAlign: 'center' }}>
              <img src={g.img} style={{ width: '100%', height: '150px', objectFit: 'cover', marginBottom: '1rem' }} />
              <h3>{g.name}</h3>
              <button onClick={() => startGame(g.id)} disabled={loading} style={{ background: loading ? '#555' : '#3b82f6', color: 'white', padding: '10px', width: '100%', border: 'none', cursor: loading ? 'wait' : 'pointer' }}>
                {loading ? 'Iniciando...' : 'Jugar'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
