import React from 'react';
// Importăm componentele router-ului (fără BrowserRouter/Router aici!)
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import './App.css';

// Importăm componentele paginilor
import PaginaInregistrare from './PaginaInregistrare';
import PaginaLogin from './PaginaLogin';
import PaginaBiblioteca from './PaginaBiblioteca';
import PaginaChestionar from './PaginaChestionar';
import PaginaMood from './PaginaMood';
import PaginaRoata from './PaginaRoata';

// Componenta principală App
function App() {
  // Hook pentru a putea naviga programatic (folosit la logout)
  // Acesta funcționează ACUM pentru că <App> este randat ÎN INTERIORUL <BrowserRouter> din index.js
  const navigate = useNavigate();

  // Funcția de Logout
  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('email');
    navigate('/login');
    alert('Te-ai deconectat cu succes.');
  };

  // JSX - Structura vizuală a aplicației
  return (
      <div className="App">
        {/* NAVBAR PROFESIONALĂ */}
        <nav className="navbar-professional">
          <div className="navbar-container">
            <div className="navbar-logo">
              <h1>📚 BookShelf AI</h1>
            </div>
            <ul className="navbar-menu">
              <li>
                <Link to="/biblioteca" className="navbar-link">
                  <span>📖</span> Biblioteca
                </Link>
              </li>
              <li>
                <Link to="/chestionar" className="navbar-link">
                  <span>✨</span> Recomandări
                </Link>
              </li>
              <li>
                <Link to="/mood" className="navbar-link">
                  <span>🎭</span> Stare
                </Link>
              </li>
              <li>
                <Link to="/roata" className="navbar-link">
                  <span>🎡</span> Roata
                </Link>
              </li>
              <li>
                <Link to="/register" className="navbar-link">
                  <span>📝</span> Înregistrare
                </Link>
              </li>
              <li>
                <Link to="/login" className="navbar-link">
                  <span>🔑</span> Login
                </Link>
              </li>
              <li>
                <button onClick={handleLogout} className="navbar-logout">
                  🚪 Logout
                </button>
              </li>
            </ul>
          </div>
        </nav>

        {/* Header-ul și Containerul Principal pentru Pagini */}
        <header className="App-header">
          <h1>Proiectul meu de Licență</h1>

          {/* Sistemul de Rutare - Aici se încarcă paginile */}
          {/* Acesta funcționează ACUM pentru că <App> este randat ÎN INTERIORUL <BrowserRouter> din index.js */}
          <Routes>
            <Route path="/" element={<PaginaBiblioteca />} />
            <Route path="/biblioteca" element={<PaginaBiblioteca />} />
            <Route path="/chestionar" element={<PaginaChestionar />} />
            <Route path="/mood" element={<PaginaMood />} />
            <Route path="/roata" element={<PaginaRoata />} />
            <Route path="/register" element={<PaginaInregistrare />} />
            <Route path="/login" element={<PaginaLogin />} />
          </Routes>
        </header>
      </div>
  );
}

// Exportăm componenta App pentru a putea fi folosită în index.js
export default App;

