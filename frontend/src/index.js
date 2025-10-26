import React from 'react';
import ReactDOM from 'react-dom/client';
// Importăm BrowserRouter din react-router-dom
import { BrowserRouter } from 'react-router-dom';
import './index.css'; // Stiluri globale (opțional)
import App from './App'; // Componenta ta principală

// Obținem elementul root din HTML (public/index.html)
const root = ReactDOM.createRoot(document.getElementById('root'));

// Randăm aplicația
root.render(
  <React.StrictMode>
    {/* Îmbrăcăm întreaga aplicație (<App>) în BrowserRouter */}
    {/* Aceasta permite componentelor din interior (inclusiv App) să folosească hook-uri ca useNavigate */}
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
// reportWebVitals(); // Poți lăsa asta comentat sau să-l ștergi
