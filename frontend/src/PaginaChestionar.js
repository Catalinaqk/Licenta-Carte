import React, { useState } from 'react';
import axios from 'axios';

// Lista de genuri predefinite
const GENURI_DISPONIBILE = ['Science Fiction', 'Fantezie', 'Mister', 'Thriller', 'Romance', 'Istoric', 'Biografie'];

function PaginaChestionar() {
  // Stări pentru formular
  const [genuriSelectate, setGenuriSelectate] = useState([]);
  const [teme, setTeme] = useState('');
  const [carteExemplu, setCarteExemplu] = useState('');
  const [limba, setLimba] = useState('ro');

  // Stări pentru rezultate și încărcare
  const [recomandari, setRecomandari] = useState(null);
  const [loadingAI, setLoadingAI] = useState(false);
  const [mesaj, setMesaj] = useState('');

  // Funcție pentru a gestiona schimbarea checkbox-urilor de gen
  const handleGenChange = (event) => {
    const gen = event.target.value;
    if (event.target.checked) {
      // Adaugă genul în listă dacă e bifat
      setGenuriSelectate([...genuriSelectate, gen]);
    } else {
      // Scoate genul din listă dacă e debifat
      setGenuriSelectate(genuriSelectate.filter(g => g !== gen));
    }
  };

  // Funcția principală care trimite datele la backend
  const handleSubmit = (event) => {
    event.preventDefault(); // Oprește reîncărcarea paginii
    setMesaj('Se generează recomandări...');
    setLoadingAI(true);
    setRecomandari(null); // Golește recomandările vechi

    const token = localStorage.getItem('token');
    if (!token) {
      alert('Trebuie să fii logat pentru a primi recomandări.');
      setLoadingAI(false);
      setMesaj('Eroare: Nu ești logat.');
      return;
    }

    // Salvează limba în localStorage pentru alte pagini
    localStorage.setItem('limba', limba);

    // Construim obiectul cu datele de trimis
    const dateChestionar = {
      genuri: genuriSelectate,
      teme: teme,
      carte_exemplu: carteExemplu, // Folosim underscore ca în Python
      limba: limba
    };

    // Trimitem datele la backend (vom crea acest endpoint la pasul următor)
    axios.post('http://localhost:5000/api/recomandari/chestionar',
        dateChestionar, // Datele din formular
        {
            headers: { 'Authorization': `Bearer ${token}` } // Trimitem token-ul
        }
    )
    .then(response => {
        setRecomandari(response.data); // Salvăm recomandările primite
        setLoadingAI(false);
        setMesaj(''); // Ștergem mesajul de încărcare
    })
    .catch(error => {
        setLoadingAI(false);
        if (error.response && error.response.data) {
             alert(`Eroare AI: ${error.response.data.error || error.response.data.msg}`);
             setMesaj(`Eroare AI: ${error.response.data.error || error.response.data.msg}`);
        } else {
             alert('Eroare la generarea recomandărilor.');
             setMesaj('Eroare la generarea recomandărilor.');
        }
    });
  };

  return (
    <div>
      <h2>Chestionar Recomandări AI</h2>
      <p>Spune-ne ce îți place și AI-ul îți va sugera următoarea lectură!</p>

      <form onSubmit={handleSubmit} style={{ border: '1px solid gray', padding: '15px', marginBottom: '20px' }}>
        {/* Selector Limbă */}
        <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: 'rgba(97, 218, 251, 0.05)', borderRadius: '8px', border: '2px solid rgba(97, 218, 251, 0.2)' }}>
          <label style={{ fontWeight: '600', marginRight: '10px' }}>🌐 Limba Recomandări:</label>
          <select value={limba} onChange={(e) => setLimba(e.target.value)} disabled={loadingAI} style={{ padding: '8px 12px', borderRadius: '6px', border: '2px solid #61dafb', backgroundColor: '#1a1825', color: '#e0e0e0', cursor: 'pointer', fontWeight: '600' }}>
            <option value="ro">🇷🇴 Română</option>
            <option value="en">🇬🇧 English</option>
          </select>
        </div>

        {/* Secțiunea Genuri */}
        <fieldset style={{ marginBottom: '15px' }}>
          <legend>Ce genuri preferi?</legend>
          {GENURI_DISPONIBILE.map(gen => (
            <div key={gen}>
              <input
                type="checkbox"
                id={`gen-${gen}`}
                value={gen}
                checked={genuriSelectate.includes(gen)}
                onChange={handleGenChange}
              />
              <label htmlFor={`gen-${gen}`}>{gen}</label>
            </div>
          ))}
        </fieldset>

        {/* Secțiunea Teme */}
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="teme">Ce teme te interesează? (separă prin virgulă)</label><br />
          <input
            type="text"
            id="teme"
            value={teme}
            onChange={(e) => setTeme(e.target.value)}
            placeholder="Ex: călătorii în timp, detectivi, magie, roboți"
            style={{ width: '80%' }}
          />
        </div>

        {/* Secțiunea Carte Exemplu */}
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="carteExemplu">O carte care ți-a plăcut mult recent? (Opțional)</label><br />
          <input
            type="text"
            id="carteExemplu"
            value={carteExemplu}
            onChange={(e) => setCarteExemplu(e.target.value)}
            placeholder="Ex: Proiectul Hail Mary"
            style={{ width: '80%' }}
          />
        </div>

        {/* Butonul de Submit */}
        <button type="submit" disabled={loadingAI}>
          {loadingAI ? 'AI-ul se gândește...' : 'Generează Recomandări'}
        </button>
      </form>

      {/* Afișarea mesajelor și a rezultatelor */}
      {mesaj && <p>{mesaj}</p>}

      {recomandari && (
        <div className="recomandari-chestionar" style={{ marginTop: '20px', border: '1px solid #00FFFF', padding: '10px' }}>
          <h3>Recomandări AI personalizate</h3>
          {recomandari.map((carte, index) => (
            <div key={index} style={{ borderBottom: '1px solid #333', padding: '10px' }}>
              <h4>{carte.titlu}</h4>
              <p><strong>Autor:</strong> {carte.autor}</p>
              <p><strong>Motivare:</strong> {carte.motivare}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default PaginaChestionar;