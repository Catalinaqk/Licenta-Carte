import React, { useState, useEffect } from 'react';
import axios from 'axios';

function PaginaBiblioteca() {
  // Starea pentru raftul personal al utilizatorului
  const [raftulMeu, setRaftulMeu] = useState([]);

  // Starea pentru formularul de căutare
  const [termenCautare, setTermenCautare] = useState('');
  const [rezultate, setRezultate] = useState([]); // Lista pentru rezultatele de la Google

  // Starea pentru recomandările AI (Similare)
  const [recomandari, setRecomandari] = useState(null);
  const [loadingAI, setLoadingAI] = useState(false);

  // Starea pentru rezultatul căutării următoarei cărți din serie
  const [nextBookResult, setNextBookResult] = useState(null);
  const [loadingNextBook, setLoadingNextBook] = useState(false);

  // Starea pentru rezumatul AI
  const [rezumatModal, setRezumatModal] = useState(null);
  const [loadingRezumat, setLoadingRezumat] = useState(false);

  // Starea pentru mesaje generale (ex: erori, logare, încărcare)
  const [mesaj, setMesaj] = useState('');


  // --- HOOK PENTRU ÎNCĂRCAREA RAFTULUI ---
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setMesaj('Te rugăm să te loghezi pentru a-ți vedea biblioteca.');
      return;
    }

    axios.get('http://localhost:5000/api/raft', { // URL corect
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(response => {
      console.log('📚 Cărți pe raft:', response.data);
      // Debug: arată ce cărți au serie
      response.data.forEach(carte => {
        if (carte.serie_nume || carte.serie_volum) {
          console.log(`✅ Carte cu serie: ${carte.titlu} - Serie: ${carte.serie_nume} Vol: ${carte.serie_volum}`);
        } else {
          console.log(`❌ Carte FĂRĂ serie: ${carte.titlu}`);
        }
      });
      setRaftulMeu(response.data);
    })
    .catch(error => {
      console.error('Eroare la încărcarea raftului:', error);
      if (error.response && (error.response.status === 401 || error.response.status === 422)) {
        setMesaj('Sesiunea ta a expirat. Te rugăm să te loghezi din nou.');
        localStorage.removeItem('token');
      } else {
        setMesaj('Eroare la încărcarea raftului.'); // Mesaj generic
      }
    });
  }, []); // [] rulează o singură dată

  // --- FUNCȚIE PENTRU CĂUTAREA CĂRȚILOR (GOOGLE BOOKS) ---
  const handleSearch = (event) => {
    event.preventDefault();
    setMesaj('Se caută...');
    setRezultate([]);
    setRecomandari(null); // Ascunde recomandările vechi la o nouă căutare
    setNextBookResult(null); // Ascunde rezultatul seriei vechi

    axios.get(`http://localhost:5000/api/search?q=${termenCautare}`)
      .then(response => {
        setRezultate(response.data);
        setMesaj(response.data.length === 0 ? 'Nu s-au găsit rezultate.' : '');
      })
      .catch(error => {
        console.error('Eroare la căutare:', error);
        let errorMsg = 'A apărut o eroare la căutare.';
        if (error.response && error.response.data && error.response.data.error) {
           errorMsg = `Eroare la căutare: ${error.response.data.error}`;
           if (error.response.data.detalii && error.response.data.detalii.error) {
               errorMsg += ` Detalii Google: ${error.response.data.detalii.error.message}`;
           }
           alert(errorMsg); // Afișăm alerta cu detalii
        }
        setMesaj(errorMsg); // Afișăm și în pagină
      });
  };

  // --- FUNCȚIE PENTRU ADĂUGAREA UNEI CĂRȚI PE RAFT ---
  const handleAddBook = (carte) => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('Trebuie să fii logat pentru a adăuga cărți!');
      return;
    }

    axios.post('http://localhost:5000/api/raft', // URL corect
      carte,
      { headers: { 'Authorization': `Bearer ${token}` } }
    )
    .then(response => {
      alert(response.data.message);
      window.location.reload(); // Reîncărcăm pagina pentru a actualiza raftul
    })
    .catch(error => {
      if (error.response && error.response.data) {
        alert(`Eroare: ${error.response.data.error || error.response.data.msg}`);
      } else {
        alert('Eroare la adăugarea cărții.');
      }
    });
  };

  // --- FUNCȚIE PENTRU RECOMANDĂRI AI (SIMILARE) ---
  const handleGetRecomandari = (carte) => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('Trebuie să fii logat pentru recomandări.');
      return;
    }
    const limba = localStorage.getItem('limba') || 'ro';
    
    setLoadingAI(true);
    setRecomandari(null);
    setNextBookResult(null); // Ascunde rezultatul seriei
    setMesaj('AI-ul generează recomandări...'); // Mesaj de încărcare

    axios.post('http://localhost:5000/api/recomandari/similar',
      { titlu: carte.titlu, autori: carte.autori, limba: limba },
      { headers: { 'Authorization': `Bearer ${token}` } }
    )
    .then(response => {
      setRecomandari(response.data);
      setLoadingAI(false);
      setMesaj(''); // Șterge mesajul de încărcare
    })
    .catch(error => {
      setLoadingAI(false);
      let errorMsg = 'Eroare la generarea recomandărilor.';
      if (error.response && error.response.data) {
        errorMsg = `Eroare AI: ${error.response.data.error || error.response.data.msg}`;
         // Afișăm detalii extra dacă sunt disponibile
         if (error.response.data.detalii) {
             errorMsg += ` Detalii: ${JSON.stringify(error.response.data.detalii)}`;
         }
      }
      alert(errorMsg);
      setMesaj(errorMsg); // Afișăm și în pagină
    });
  };

  // --- FUNCȚIE PENTRU ȘTERGEREA UNEI CĂRȚI DE PE RAFT ---
  const handleDeleteBook = (id_raft_de_sters) => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('Trebuie să fii logat pentru a șterge cărți.');
      return;
    }
    if (!window.confirm('Ești sigur că vrei să ștergi această carte din bibliotecă?')) {
      return;
    }

    axios.delete(`http://localhost:5000/api/raft/${id_raft_de_sters}`, { // URL corect cu ID
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(response => {
      alert(response.data.message);
      // Actualizăm starea locală FĂRĂ refresh
      setRaftulMeu(raftulMeuActual => raftulMeuActual.filter(carte => carte.id_raft !== id_raft_de_sters));
    })
    .catch(error => {
      console.error('Eroare la ștergerea cărții:', error);
      if (error.response && error.response.data) {
        alert(`Eroare: ${error.response.data.error || error.response.data.msg}`);
      } else {
        alert('Eroare la ștergerea cărții.');
      }
    });
  };

  // --- FUNCȚIE PENTRU A GĂSI URMĂTOAREA CARTE DIN SERIE ---
  const handleFindNextInSeries = (id_raft_carte_curenta) => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('Trebuie să fii logat.');
      return;
    }
    console.log('📚 Start căutare serie pentru id_raft:', id_raft_carte_curenta);
    setLoadingNextBook(true);
    setNextBookResult(null);
    setRecomandari(null); // Ascunde recomandările similare
    setMesaj('Se caută următoarea carte...');

    axios.post('http://localhost:5000/api/recomandari/serie',
      { id_raft: id_raft_carte_curenta },
      { headers: { 'Authorization': `Bearer ${token}` } }
    )
    .then(response => {
      console.log('✅ Răspuns API serie:', response.data);
      setNextBookResult(response.data);
      setLoadingNextBook(false);
      setMesaj('');
    })
    .catch(error => {
      setLoadingNextBook(false);
      let errorMsg = 'Eroare la găsirea următoarei cărți.';
      if (error.response) {
        console.error('❌ Eroare API status:', error.response.status);
        console.error('❌ Eroare API data:', error.response.data);
        errorMsg = `Eroare: ${error.response.data?.error || error.response.data?.msg || error.response.statusText}`;
      } else {
        console.error('❌ Eroare de conexiune:', error.message);
      }
      setNextBookResult({ error: errorMsg }); // Salvăm eroarea pentru afișare
      setMesaj('');
      console.error('Eroare completa find next:', error);
    });
  };

  // --- FUNCȚIE PENTRU GENERARE REZUMAT AI ---
  const handleGenerateRezumat = (carte) => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('Trebuie să fii logat.');
      return;
    }

    const limba = localStorage.getItem('limba') || 'ro';

    console.log(`📖 Generez rezumat pentru: ${carte.titlu}`);
    setLoadingRezumat(true);
    setRezumatModal(null);
    setMesaj('Se generează rezumat...');

    axios.post('http://localhost:5000/api/recomandari/rezumat',
      {
        titlu: carte.titlu,
        autor: carte.autori,
        descriere: carte.descriere || '',
        limba: limba
      },
      { headers: { 'Authorization': `Bearer ${token}` } }
    )
    .then(response => {
      console.log('✅ Rezumat generat:', response.data);
      setRezumatModal({
        titlu: response.data.titlu,
        autor: response.data.autor,
        rezumat: response.data.rezumat
      });
      setLoadingRezumat(false);
      setMesaj('');
    })
    .catch(error => {
      setLoadingRezumat(false);
      let errorMsg = 'Eroare la generarea rezumatului.';
      if (error.response) {
        console.error('❌ Eroare API status:', error.response.status);
        console.error('❌ Eroare API data:', error.response.data);
        errorMsg = `Eroare: ${error.response.data?.error || error.response.data?.msg || 'Nu am putut genera rezumatul'}`;
      } else {
        console.error('❌ Eroare de conexiune:', error.message);
      }
      alert(errorMsg);
      setMesaj('');
    });
  };

  // --- AFIȘAREA VIZUALĂ (JSX) ---
  return (
    <div>
      {/* --- SECȚIUNEA DE CĂUTARE CĂRȚI (MOVED TO TOP) --- */}
      <div className="search-section-top">
        <h2>🔍 Caută Cărți</h2>
        <form onSubmit={handleSearch} className="search-form-top">
          <input
            type="text"
            value={termenCautare}
            onChange={(e) => setTermenCautare(e.target.value)}
            placeholder="Ex: Dune, Stăpânul Inelelor, Harry Potter..."
            required
          />
          <button type="submit" className="btn-search-top">Caută</button>
        </form>
      </div>

      {/* --- SECȚIUNEA RAFTUL MEU --- */}
      <hr style={{ margin: '20px 0' }} />
      <h2>📚 Raftul Meu</h2>
      <div className="raftul-meu">
        {raftulMeu.length > 0 ? (
          raftulMeu.map((carte) => (
            // Cardul pentru fiecare carte de pe raft
            <div key={carte.id_raft} className="book-card"> {/* Adăugăm o clasă pentru stilizare */}
              <img
                 src={carte.url_coperta || 'https://placehold.co/200x300/3a3f47/61dafb?text=Fara+Coperta'} // Placeholder
                 alt={`Coperta ${carte.titlu}`}
                 onError={(e) => { e.target.onerror = null; e.target.src='https://placehold.co/200x300/3a3f47/61dafb?text=Fara+Coperta'; }} // Fallback dacă imaginea nu se încarcă
               />
              <h4>{carte.titlu}</h4>
              <p className="book-author">{carte.autori}</p> {/* Clasă pentru autori */}
              <p className="book-status">Status: {carte.status}</p> {/* Clasă pentru status */}

              {/* Butoanele de acțiune */}
              <div className="book-actions"> {/* Container pentru butoane */}
                <button
                  onClick={() => handleGetRecomandari(carte)}
                  disabled={loadingAI || loadingNextBook || loadingRezumat}
                  className="btn-recommend"> {/* Clasă pentru stil */}
                  {loadingAI ? 'Se gândește...' : 'Recomandă Similare'}
                </button>

                {/* Butonul "Găsește Următoarea" - apare pentru ORICE carte (backend va căuta seria) */}
                <button
                  onClick={() => handleFindNextInSeries(carte.id_raft)}
                  disabled={loadingAI || loadingNextBook || loadingRezumat}
                  className="btn-next-series"> {/* Clasă pentru stil */}
                  {loadingNextBook ? 'Se caută...' : 'Găsește Următoarea'}
                </button>

                {/* Butonul Rezumat AI */}
                <button
                  onClick={() => handleGenerateRezumat(carte)}
                  disabled={loadingAI || loadingNextBook || loadingRezumat}
                  className="btn-summary"> {/* Clasă pentru stil */}
                  {loadingRezumat ? 'Se generează...' : 'Rezumat AI'}
                </button>

                {/* Butonul Șterge */}
                <button
                  onClick={() => handleDeleteBook(carte.id_raft)}
                  disabled={loadingAI || loadingNextBook || loadingRezumat}
                  className="btn-delete"> {/* Clasă pentru stil */}
                  Șterge
                </button>
              </div>
            </div>
          ))
        ) : (
          // Mesaj dacă raftul e gol
          <p>{mesaj || 'Raftul tău este gol. Caută o carte mai jos și adaug-o.'}</p>
        )}
      </div>

      {/* --- SECȚIUNEA REZULTAT SERIE --- */}
      {loadingNextBook && <p style={{textAlign: 'center', margin: '20px'}}>Se caută seria completă...</p>}
      {nextBookResult && (
        <div className={`result-box ${nextBookResult.error ? 'result-error' : 'result-success'}`}>
          <h3>📚 {nextBookResult.error ? 'Eroare' : `Seria: ${nextBookResult.seria_nume}`}</h3>
          {nextBookResult.error ? (
            <p>Eroare: {nextBookResult.error}</p>
          ) : (
            <div>
              <p style={{marginBottom: '15px', fontStyle: 'italic', color: '#aaa'}}>
                Total cărți: {nextBookResult.carti ? nextBookResult.carti.length : 0}
              </p>
              {nextBookResult.carti && nextBookResult.carti.map((carte, index) => (
                <div key={index} className="serie-item" style={{
                  borderLeft: '4px solid #52c41a',
                  paddingLeft: '15px',
                  marginBottom: '12px',
                  paddingBottom: '12px',
                  borderBottom: '1px solid #444'
                }}>
                  <p style={{margin: '0 0 5px 0'}}>
                    <strong style={{color: '#52c41a', fontSize: '1.1em'}}>
                      📖 Cartea {carte.volum}
                    </strong>
                  </p>
                  <p style={{margin: '3px 0'}}><strong>Titlu:</strong> {carte.titlu}</p>
                  <p style={{margin: '3px 0'}}><strong>Autor:</strong> {carte.autor}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* --- SECȚIUNEA RECOMANDĂRI AI (SIMILARE) --- */}
      {loadingAI && <p style={{textAlign: 'center', margin: '20px'}}>AI-ul generează recomandări...</p>}
      {recomandari && (
        <div className="result-box result-success"> {/* Clasă pentru stil */}
          <h3>Recomandări AI Similare</h3>
          {recomandari.map((carte, index) => (
            <div key={index} className="recommendation-item"> {/* Clasă pentru stil */}
              <h4>{carte.titlu}</h4>
              <p><strong>Autor:</strong> {carte.autor}</p>
              <p><strong>Motivare:</strong> {carte.motivare}</p>
            </div>
          ))}
        </div>
      )}

      {/* --- MODAL REZUMAT AI --- */}
      {rezumatModal && (
        <div className="modal-overlay" onClick={() => setRezumatModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setRezumatModal(null)}>✕</button>
            <h2>📖 Rezumat AI</h2>
            <h3>{rezumatModal.titlu}</h3>
            <p className="modal-author">de {rezumatModal.autor}</p>
            <div className="modal-rezumat">
              {rezumatModal.rezumat}
            </div>
            <button className="btn-close-modal" onClick={() => setRezumatModal(null)}>Închide</button>
          </div>
        </div>
      )}

      {/* Afișează mesajul general (ex: 'Nu s-au găsit rezultate') */}
      {mesaj && !(loadingAI || loadingNextBook) && <p>{mesaj}</p>} {/* Nu afișa dacă se încarcă AI */}

      {/* --- SECȚIUNEA REZULTATE CĂUTARE --- */}
      {rezultate.length > 0 && (
        <div className="search-results-section">
          <h2>🔍 Rezultate Căutare</h2>
          <div className="rezultate-cautare">
            {rezultate.map((carte) => (
              <div key={carte.id_google} className="search-result-item">
                <img
                   src={carte.url_coperta || 'https://placehold.co/200x300/3a3f47/61dafb?text=Fara+Coperta'}
                   alt={`Coperta ${carte.titlu}`}
                   onError={(e) => { e.target.onerror = null; e.target.src='https://placehold.co/200x300/3a3f47/61dafb?text=Fara+Coperta'; }}
                 />
                <h3>{carte.titlu}</h3>
                <p className="search-author">{carte.autori.join(', ')}</p>
                <button onClick={() => handleAddBook(carte)} className="btn-add-search">
                  ➕ Adaugă în Bibliotecă
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default PaginaBiblioteca;
