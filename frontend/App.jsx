import { useState } from 'react';

// LISTA DE JUEGOS (Debe coincidir con los archivos en tu AMI)
const GAMES = [
  { id: 'SuperMarioWorld.smc', name: 'Super Mario World', img: 'https://upload.wikimedia.org/wikipedia/en/3/32/Super_Mario_World_Coverart.png' },
  { id: 'DonkeyKongCountry.sfc', name: 'Donkey Kong Country', img: 'https://upload.wikimedia.org/wikipedia/en/c/c1/Donkey_Kong_Country_SNES_cover.png' },
  { id: 'ZeldaALinkToThePast.sfc', name: 'Zelda: A Link to the Past', img: 'https://upload.wikimedia.org/wikipedia/en/2/21/The_Legend_of_Zelda_A_Link_to_the_Past_SNES_Game_Cover.jpg' }
];

// Detección automática de API:
// Si estamos en desarrollo (localhost:5173), usa localhost:8000.
// Si estamos en producción (servido desde el backend), usa ruta relativa vacía "".
const IS_DEV = import.meta.env.DEV;
const API_BASE = IS_DEV ? 'http://localhost:8000' : '';

export default function App() {
  const [activeSession, setActiveSession] = useState(null);
  const [loading, setLoading] = useState(false);

  const startGame = async (gameId) => {
    setLoading(true);
    try {
      // Llamada al endpoint relativo o absoluto según entorno
      const res = await fetch(`${API_BASE}/games/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_filename: gameId })
      });
      
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || res.statusText);
      }

      const data = await res.json();
      setActiveSession(data);
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const stopGame = async () => {
    if (!activeSession) return;
    if(!confirm("¿Apagar máquina?")) return;
    
    try {
      await fetch(`${API_BASE}/sessions/${activeSession.instance_id || activeSession.id}`, { method: 'DELETE' });
      setActiveSession(null);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#111', color: 'white', fontFamily: 'sans-serif', padding: '2rem' }}>
      <h1 style={{ textAlign: 'center', color: '#a855f7', marginBottom: '3rem' }}>☁️ RetroCloud</h1>

      {activeSession ? (
        <div style={{ maxWidth: '500px', margin: '0 auto', background: '#222', padding: '2rem', borderRadius: '12px', border: '1px solid #333' }}>
          <h2 style={{ color: '#4ade80', marginTop: 0 }}>✅ Servidor Listo</h2>
          <div style={{ background: '#000', padding: '1rem', borderRadius: '8px', fontFamily: 'monospace', margin: '1.5rem 0' }}>
            <p style={{ margin: '5px 0' }}>🔗 <a href={activeSession.url} target="_blank" style={{ color: '#60a5fa' }}>{activeSession.url}</a></p>
            <p style={{ margin: '5px 0' }}>👤 {activeSession.user}</p>
            <p style={{ margin: '5px 0' }}>🔑 {activeSession.pass}</p>
          </div>
          <p style={{ fontSize: '0.9rem', color: '#facc15' }}>⚠️ Acepta la advertencia de seguridad del navegador al entrar.</p>
          <button onClick={stopGame} style={{ width: '100%', padding: '12px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
            Apagar Máquina
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '2rem' }}>
          {GAMES.map(game => (
            <div key={game.id} style={{ background: '#222', borderRadius: '12px', overflow: 'hidden', transition: 'transform 0.2s' }}>
              <img src={game.img} alt={game.name} style={{ width: '100%', height: '180px', objectFit: 'cover' }} />
              <div style={{ padding: '1.5rem' }}>
                <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.2rem' }}>{game.name}</h3>
                <button 
                  onClick={() => startGame(game.id)}
                  disabled={loading}
                  style={{ width: '100%', padding: '10px', background: loading ? '#444' : '#3b82f6', color: 'white', border: 'none', borderRadius: '6px', cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 'bold' }}
                >
                  {loading ? 'Iniciando...' : 'Jugar Ahora'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
