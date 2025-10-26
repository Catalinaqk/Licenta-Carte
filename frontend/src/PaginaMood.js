import React, { useState } from 'react';
import axios from 'axios';

function PaginaMood() {
  const [stareSelectata, setStareSelectata] = useState(null);
  const [stareCustom, setStareCustom] = useState('');
  const [recomandari, setRecomandari] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mesaj, setMesaj] = useState('');
  const [limba, setLimba] = useState('ro');

  // Lista de stări disponibile cu descrieri
  const stari = [
    { id: 'amuzant', emoji: '😂', titlu: 'Amuzant & Relaxant', descriere: 'Ceva cu umor și ușurință' },
    { id: 'thriller', emoji: '😱', titlu: 'Thriller Captivant', descriere: 'Suspans și mister' },
    { id: 'dragoste', emoji: '💔', titlu: 'Dragoste Tristă', descriere: 'Emoție și melancolie' },
    { id: 'aventura', emoji: '🗺️', titlu: 'Aventură Épică', descriere: 'Acțiune și descoperire' },
    { id: 'mistery', emoji: '🔍', titlu: 'Mister Captivant', descriere: 'Crimă și investigație' },
    { id: 'fantasia', emoji: '✨', titlu: 'Fantasia Magică', descriere: 'Lumi imaginare și magie' },
    { id: 'personal', emoji: '🌟', titlu: 'Dezvoltare Personală', descriere: 'Inspirație și motivație' },
  ];

  // Funcția care apelează API-ul pentru recomandări
  const handleMoodClick = (moodId) => {
    setStareSelectata(moodId);
    setStareCustom(''); // Clear custom input
    setRecomandari(null);
    setMesaj(limba === 'ro' ? 'Se generează recomandări...' : 'Generating recommendations...');
    setLoading(true);

    axios.post('http://localhost:5000/api/recomandari/mood', {
      stare: moodId,
      limba: limba
    })
      .then(response => {
        console.log('✅ Recomandări primite:', response.data);
        // API retorna fie array direct, fie obiect cu cheie 'recomandari'
        const recomandariData = Array.isArray(response.data) ? response.data : response.data.recomandari || response.data;
        setRecomandari(recomandariData);
        setMesaj('');
        setLoading(false);
      })
      .catch(error => {
        console.error('❌ Eroare:', error);
        let errorMsg = limba === 'ro' ? 'A apărut o eroare la generarea recomandărilor.' : 'An error occurred while generating recommendations.';
        if (error.response && error.response.data && error.response.data.error) {
          errorMsg = `${limba === 'ro' ? 'Eroare' : 'Error'}: ${error.response.data.error}`;
        }
        setMesaj(errorMsg);
        setRecomandari(null);
        setLoading(false);
      });
  };

  // Handler pentru stări custom
  const handleCustomMood = () => {
    if (!stareCustom.trim()) {
      setMesaj(limba === 'ro' ? 'Te rog să descrii starea ta' : 'Please describe your mood');
      return;
    }

    setStareSelectata(null);
    setRecomandari(null);
    setMesaj(limba === 'ro' ? 'Se generează recomandări...' : 'Generating recommendations...');
    setLoading(true);

    axios.post('http://localhost:5000/api/recomandari/mood', {
      stare_custom: stareCustom,
      limba: limba
    })
      .then(response => {
        console.log('✅ Recomandări primite:', response.data);
        // API retorna fie array direct, fie obiect cu cheie 'recomandari'
        const recomandariData = Array.isArray(response.data) ? response.data : response.data.recomandari || response.data;
        setRecomandari(recomandariData);
        setMesaj('');
        setLoading(false);
      })
      .catch(error => {
        console.error('❌ Eroare:', error);
        let errorMsg = limba === 'ro' ? 'A apărut o eroare la generarea recomandărilor.' : 'An error occurred while generating recommendations.';
        if (error.response && error.response.data && error.response.data.error) {
          errorMsg = `${limba === 'ro' ? 'Eroare' : 'Error'}: ${error.response.data.error}`;
        }
        setMesaj(errorMsg);
        setRecomandari(null);
        setLoading(false);
      });
  };

  const resetare = () => {
    setStareSelectata(null);
    setStareCustom('');
    setRecomandari(null);
    setMesaj('');
  };

  return (
    <div className="mood-page">
      {/* Header */}
      <div className="mood-header">
        <h1>🎭 Ce Stare Emoțională Ai?</h1>
        <p>Alege cum te simți și primește recomandări personalizate de cărți</p>
        
        {/* Selector limbă */}
        <div className="lingua-selector">
          <label>🌐 Limba:</label>
          <select value={limba} onChange={(e) => setLimba(e.target.value)} disabled={loading}>
            <option value="ro">🇷🇴 Română</option>
            <option value="en">🇬🇧 English</option>
          </select>
        </div>
      </div>

      {/* Butoane pentru stări */}
      <div className="mood-buttons-container">
        {stari.map((stare) => (
          <button
            key={stare.id}
            className={`mood-button ${stareSelectata === stare.id ? 'active' : ''}`}
            onClick={() => handleMoodClick(stare.id)}
            disabled={loading}
          >
            <div className="mood-emoji">{stare.emoji}</div>
            <div className="mood-title">{stare.titlu}</div>
            <div className="mood-desc">{stare.descriere}</div>
          </button>
        ))}
      </div>

      {/* Custom Mood Input */}
      <div className="custom-mood-section">
        <h3>✍️ Sau Descrie-ți Propria Stare</h3>
        <p className="custom-mood-hint">{limba === 'ro' ? 'Ex: Mi-ar plăcea ceva pentru vreme ploioasă, Stare de toamnă melancolică, Cărți inspiraționale...' : 'E.g: Something for rainy weather, Autumn melancholy mood, Inspirational books...'}</p>
        <textarea
          className="custom-mood-input"
          value={stareCustom}
          onChange={(e) => setStareCustom(e.target.value.slice(0, 500))}
          placeholder={limba === 'ro' ? 'Descrie starea ta emoțională, sezonul, atmosfera...' : 'Describe your emotional state, season, atmosphere...'}
          disabled={loading}
          maxLength={500}
        />
        <div className="custom-mood-footer">
          <span className="char-count">{stareCustom.length}/500</span>
          <button 
            onClick={handleCustomMood} 
            className="btn-custom-mood"
            disabled={loading || !stareCustom.trim()}
          >
            🚀 {limba === 'ro' ? 'Caută Recomandări' : 'Get Recommendations'}
          </button>
        </div>
      </div>

      {/* Loading indicator */}
      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Se caută cele mai potrivite cărți pentru tine...</p>
        </div>
      )}

      {/* Mesaje */}
      {mesaj && !loading && (
        <div className="mood-message error">
          {mesaj}
        </div>
      )}

      {/* Recomandări */}
      {recomandari && recomandari.length > 0 && (
        <div className="mood-results">
          <div className="mood-results-header">
            <h2>📚 Cărți Recomandate pentru Tine</h2>
            <button onClick={resetare} className="btn-new-mood">
              🔄 Schimbă Starea
            </button>
          </div>

          <div className="recomandari-grid">
            {recomandari.map((carte, index) => (
              <div key={index} className="recomandare-card">
                <div className="recomandare-number">
                  <span className="number-badge">{index + 1}</span>
                </div>
                <h3 className="recomandare-titlu">{carte.titlu || carte.title || 'N/A'}</h3>
                <p className="recomandare-autor">
                  <strong>👤 de</strong> {carte.autor || carte.author || 'N/A'}
                </p>
                <p className="recomandare-motivare">
                  <strong>💡 De ce?</strong> {carte.motivare || carte.reason || 'N/A'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !recomandari && stareSelectata && (
        <div className="mood-empty">
          <p>Alege o stare pentru a vedea recomandări</p>
        </div>
      )}
    </div>
  );
}

export default PaginaMood;
