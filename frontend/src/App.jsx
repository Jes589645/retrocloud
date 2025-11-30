import { useState } from 'react';
// Importamos el JSON generado por el script de Python
import GAMES_CATALOG from './assets/games_catalog.json'; 

export default function App() {
  const [activeSession, setActiveSession] = useState(null);
  const [loading, setLoading] = useState(false);

  // Usamos el catálogo importado directamente
  const games = GAMES_CATALOG;

  const startGame = async (gameId) => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/games/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_filename: gameId })
      });
      
      if (!res.ok) throw new Error('Error en el backend');
      
      const data = await res.json();
      setActiveSession(data);
    } catch (error) {
      alert('Error lanzando el juego: ' + error);
    } finally {
      setLoading(false);
    }
  };

  // ... (Resto del código igual: stopGame y el return del JSX) ...
  
  return (
    // ... (Header) ...
      {activeSession ? (
        // ... (Vista de sesión activa igual) ...
      ) : (
        /* VISTA DE CATÁLOGO DINÁMICA */
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem' }}>
          {games.length === 0 ? (
             <p style={{color: '#888'}}>No se encontraron juegos. Ejecuta generate_catalog.py</p>
          ) : (
             games.map(g => (
              <div key={g.id} style={{ background: '#2d2d2d', borderRadius: '10px', overflow: 'hidden', textAlign: 'center' }}>
                <img src={g.img} alt={g.name} style={{ width: '100%', height: '150px', objectFit: 'cover' }} />
                <div style={{ padding: '1rem' }}>
                  <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>{g.name}</h3>
                  <button 
                    onClick={() => startGame(g.id)}
                    disabled={loading}
                    style={{ 
                      background: loading ? '#555' : '#3b82f6', 
                      color: 'white', border: 'none', padding: '10px', width: '100%', cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 'bold' 
                    }}
                  >
                    {loading ? 'Iniciando...' : 'Jugar Ahora'}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
