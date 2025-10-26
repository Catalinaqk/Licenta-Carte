import React, { useState, useEffect } from 'react';
import axios from 'axios';

function PaginaRoata() {
  const [carti, setCarti] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mesaj, setMesaj] = useState('');
  const [spinning, setSpinning] = useState(false);
  const [cartieSelectata, setCartieSelectata] = useState(null);
  const [rotationAngle, setRotationAngle] = useState(0);

  // Încarcă cărțile din raft la montare
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setMesaj('Te rugăm să te loghezi pentru a vedea biblioteca.');
      setLoading(false);
      return;
    }

    axios.get('http://localhost:5000/api/raft', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(response => {
      console.log('📚 Cărți încărcate:', response.data);
      setCarti(response.data);
      if (response.data.length === 0) {
        setMesaj('Biblioteca ta este goală. Adaugă cărți pentru a folosi roata!');
      } else {
        setMesaj('');
      }
      setLoading(false);
    })
    .catch(error => {
      console.error('Eroare la încărcarea raftului:', error);
      let errorMsg = 'Eroare la încărcarea cărților.';
      if (error.response && (error.response.status === 401 || error.response.status === 422)) {
        errorMsg = 'Sesiunea ta a expirat. Te rugăm să te loghezi din nou.';
        localStorage.removeItem('token');
      }
      setMesaj(errorMsg);
      setLoading(false);
    });
  }, []);

  // Funcție pentru a învârte roata
  const handleSpin = () => {
    if (carti.length === 0) {
      setMesaj('Nu ai cărți în bibliotecă!');
      return;
    }

    if (spinning) return;

    setSpinning(true);
    setCartieSelectata(null);

    // Generează un unghi random (minim 5 rotații complete + offset)
    const rotations = 5 + Math.random() * 5; // 5-10 rotații
    const randomAngle = Math.random() * 360;
    const totalAngle = rotations * 360 + randomAngle;

    setRotationAngle(totalAngle);

    // După ce se termină rotația (3.5 secunde), selectează cartea
    setTimeout(() => {
      // Calculează poziția finale (normalizează la 0-360)
      const finalAngle = totalAngle % 360;
      
      // Fiecare carte ocupă 360/numCarti grade
      const degPerCarte = 360 / carti.length;
      
      // Cartea selectată este cea la vârf (unghiul 0 în roată, dar inversez pentru că roata merge invers)
      const indexSelectat = Math.floor((360 - finalAngle) / degPerCarte) % carti.length;
      
      setCartieSelectata(carti[indexSelectat]);
      setSpinning(false);
    }, 3500);
  };

  if (loading) {
    return (
      <div className="roata-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Se încarcă biblioteca...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="roata-page">
      <div className="roata-container">
        <h1>🎡 Roata Cărților</h1>
        <p className="roata-subtitle">Lasă roata să-ți aleagă o carte de citit din biblioteca ta!</p>

        {mesaj && <div className="roata-message error">{mesaj}</div>}

        {carti.length > 0 ? (
          <div className="roata-content">
            {/* ROATA */}
            <div className="roata-wrapper">
              <div className="roata-pointer">▼</div>
              <svg
                className={`roata ${spinning ? 'spinning' : ''}`}
                style={{ transform: `rotate(${rotationAngle}deg)` }}
                viewBox="0 0 400 400"
                width="400"
                height="400"
              >
                {carti.map((carte, index) => {
                  const totalCarti = carti.length;
                  const anglePerSection = 360 / totalCarti;
                  const startAngle = (index * anglePerSection) * (Math.PI / 180);
                  const endAngle = ((index + 1) * anglePerSection) * (Math.PI / 180);

                  const radius = 160;
                  const labelRadius = 110;

                  // Calculează punctele arcului
                  const x1 = 200 + radius * Math.cos(startAngle - Math.PI / 2);
                  const y1 = 200 + radius * Math.sin(startAngle - Math.PI / 2);
                  const x2 = 200 + radius * Math.cos(endAngle - Math.PI / 2);
                  const y2 = 200 + radius * Math.sin(endAngle - Math.PI / 2);

                  const largeArc = anglePerSection > 180 ? 1 : 0;

                  const pathData = [
                    `M 200 200`,
                    `L ${x1} ${y1}`,
                    `A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`,
                    'Z'
                  ].join(' ');

                  // Culori alternante
                  const colors = ['#61dafb', '#52c41a', '#ff7a45', '#f5222d', '#722ed1', '#eb2f96'];
                  const color = colors[index % colors.length];

                  // Calculează poziția textului
                  const midAngle = startAngle + (endAngle - startAngle) / 2;
                  const textX = 200 + labelRadius * Math.cos(midAngle - Math.PI / 2);
                  const textY = 200 + labelRadius * Math.sin(midAngle - Math.PI / 2);
                  const textRotation = (midAngle * 180 / Math.PI) - 90;

                  return (
                    <g key={index}>
                      <path
                        d={pathData}
                        fill={color}
                        stroke="white"
                        strokeWidth="2"
                        opacity="0.85"
                      />
                      <text
                        x={textX}
                        y={textY}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="white"
                        fontSize="12"
                        fontWeight="bold"
                        transform={`rotate(${textRotation} ${textX} ${textY})`}
                        style={{ userSelect: 'none', pointerEvents: 'none' }}
                      >
                        {carte.titlu.substring(0, 15)}
                        {carte.titlu.length > 15 ? '...' : ''}
                      </text>
                    </g>
                  );
                })}

                {/* Cerc central */}
                <circle cx="200" cy="200" r="30" fill="#0f0c29" stroke="#61dafb" strokeWidth="3" />
                <text
                  x="200"
                  y="200"
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="#61dafb"
                  fontSize="20"
                  fontWeight="bold"
                  style={{ pointerEvents: 'none' }}
                >
                  🎲
                </text>
              </svg>
            </div>

            {/* BUTON ROATĂ */}
            <button
              onClick={handleSpin}
              disabled={spinning}
              className="btn-spin"
            >
              {spinning ? '⏳ Se învârte...' : '🎯 Dă-i Drumul!'}
            </button>

            {/* CARTEA SELECTATĂ */}
            {cartieSelectata && (
              <div className="roata-result">
                <h2>✨ Cartea Aleasă pentru Tine! ✨</h2>
                <div className="result-book-card">
                  {cartieSelectata.url_coperta && (
                    <img
                      src={cartieSelectata.url_coperta}
                      alt={cartieSelectata.titlu}
                      className="result-book-cover"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = 'https://placehold.co/150x220/3a3f47/61dafb?text=Fara+Coperta';
                      }}
                    />
                  )}
                  <div className="result-book-info">
                    <h3>{cartieSelectata.titlu}</h3>
                    <p className="book-author">de {cartieSelectata.autori}</p>
                    <p className="book-status">Status: {cartieSelectata.status}</p>
                    <p className="suggestion-text">
                      "Azi e ziua perfectă pentru a citi aceasta carte! 📖"
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* LISTA CĂRȚILOR */}
            <div className="roata-books-list">
              <h3>📚 Cărțile în roată ({carti.length})</h3>
              <div className="books-grid">
                {carti.map((carte, index) => (
                  <div key={carte.id_raft} className="small-book-card">
                    <img
                      src={carte.url_coperta || 'https://placehold.co/100x150/3a3f47/61dafb?text=Fara+Coperta'}
                      alt={carte.titlu}
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = 'https://placehold.co/100x150/3a3f47/61dafb?text=Fara+Coperta';
                      }}
                    />
                    <p className="small-book-title">{carte.titlu}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="roata-empty">
            <p>Nu ai cărți în bibliotecă pentru a folosi roata. Adaugă cărți pentru a continua!</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default PaginaRoata;
