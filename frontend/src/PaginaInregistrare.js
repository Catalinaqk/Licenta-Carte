import React, { useState } from 'react';
import axios from 'axios';

function PaginaInregistrare() {
  // Stări pentru a ține minte ce scrie utilizatorul în formular
  const [email, setEmail] = useState('');
  const [parola, setParola] = useState('');
  const [mesaj, setMesaj] = useState(''); // Pentru a afișa mesaje de succes/eroare

  // Funcția care se apelează la trimiterea formularului
  const handleRegister = (event) => {
    event.preventDefault(); // Oprește reîncărcarea paginii
    setMesaj('Se procesează...');

    // Trimite datele către backend-ul Python
    axios.post('http://localhost:5000/api/register', {
      email: email,
      parola: parola
    })
    .then(response => {
      // Răspuns de succes de la server
      setMesaj(response.data.message);
      setEmail('');
      setParola('');
    })
    .catch(error => {
      // Răspuns de eroare de la server
      if (error.response) {
        setMesaj(`Eroare: ${error.response.data.error}`);
      } else {
        setMesaj('Eroare la conectare.');
      }
    });
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>📝 Înregistrare</h1>
          <p>Alătură-te comunității BookShelf!</p>
        </div>
        
        <form onSubmit={handleRegister} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">📧 Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Introdu emailul tău"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">🔐 Parolă</label>
            <input
              id="password"
              type="password"
              value={parola}
              onChange={(e) => setParola(e.target.value)}
              placeholder="Alege o parolă sigură"
              required
            />
          </div>

          <button type="submit" className="btn-auth">
            ✨ Creează cont
          </button>
        </form>

        {mesaj && (
          <div className={`auth-message ${mesaj.includes('reușit') || mesaj.includes('succes') ? 'success' : 'error'}`}>
            {mesaj}
          </div>
        )}

        <div className="auth-footer">
          <p>Ai deja cont? <a href="/login">Conectează-te!</a></p>
        </div>
      </div>
    </div>
  );
}

export default PaginaInregistrare;