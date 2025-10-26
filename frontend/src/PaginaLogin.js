import React, { useState } from 'react';
import axios from 'axios';

function PaginaLogin() {
  const [email, setEmail] = useState('');
  const [parola, setParola] = useState('');
  const [mesaj, setMesaj] = useState('');

  const handleLogin = (event) => {
    event.preventDefault();
    setMesaj('Se procesează...');

    axios.post('http://localhost:5000/api/login', {
      email: email,
      parola: parola
    })
    .then(response => {
      // --- SUCCES! ---
      setMesaj(response.data.message);
      
      // --- LINIILE VITALE ---
      // Salvăm token-ul. Ne bazăm că serverul trimite 'response.data.token'
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('email', response.data.email);
      // ----------------------------------------
      
      setEmail('');
      setParola('');
      
      // --- REDIRECȚIONAREA ---
      // Folosim 'window.location.href' care forțează o reîncărcare completă.
      // Asta e bine, pentru că PaginaBiblioteca va citi noul localStorage.
      alert('Login reușit! Vei fi redirecționat.');
      window.location.href = '/biblioteca'; 

    })
    .catch(error => {
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
          <h1>🔑 Autentificare</h1>
          <p>Bine ai venit înapoi!</p>
        </div>
        
        <form onSubmit={handleLogin} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">📧 Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Tu email"
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
              placeholder="Parola ta"
              required
            />
          </div>

          <button type="submit" className="btn-auth">
            🚀 Intră în cont
          </button>
        </form>

        {mesaj && (
          <div className={`auth-message ${mesaj.includes('reușit') ? 'success' : 'error'}`}>
            {mesaj}
          </div>
        )}

        <div className="auth-footer">
          <p>Nu ai cont? <a href="/register">Înregistrează-te acum!</a></p>
        </div>
      </div>
    </div>
  );
}

export default PaginaLogin;