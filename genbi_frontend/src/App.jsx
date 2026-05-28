import React, { useState } from 'react'
import { Sparkles, Terminal, Activity, Database, BarChart3 } from 'lucide-react'

function App() {
  return (
    <div className="app-container">
      {/* Effets lumineux d'arrière-plan pour le rendu premium */}
      <div className="bg-glow bg-glow-blue"></div>
      <div className="bg-glow bg-glow-purple"></div>

      <header className="app-header">
        <div className="logo-section">
          <Sparkles className="logo-icon text-glow" />
          <span className="logo-text">GenBI</span>
        </div>
        <div className="status-badge">
          <Activity className="status-icon pulsate" />
          <span>Plateforme Connectée</span>
        </div>
      </header>

      <main className="welcome-hero">
        <h1 className="hero-title">
          Discutez avec vos données <br />
          <span className="gradient-text">de manière souveraine</span>
        </h1>
        <p className="hero-subtitle">
          Une plateforme de Business Intelligence Générative 100% open-source, 
          ultra-sécurisée et pilotée par les métadonnées de votre pipeline dbt.
        </p>

        <div className="card-grid">
          <div className="feature-card">
            <Database className="card-icon" />
            <h3>PostgreSQL & dbt</h3>
            <p>Données modélisées en schémas staging/marts et documentées comme code.</p>
          </div>
          <div className="feature-card">
            <Terminal className="card-icon" />
            <h3>Agent Local Ollama</h3>
            <p>Traduction SQL sécurisée et privée s'exécutant localement sur votre matériel.</p>
          </div>
          <div className="feature-card">
            <BarChart3 className="card-icon" />
            <h3>Visualisations interactives</h3>
            <p>Génération automatique de graphiques Recharts basés sur les analyses de l'IA.</p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
