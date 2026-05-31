import { useState } from 'react'
import { Sparkles, Activity, LogOut } from 'lucide-react'
import { ChatWindow } from './components/chat/ChatWindow'
import { LoginPage } from './components/auth/LoginPage'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => !!localStorage.getItem('genbi_token')
  )

  function handleLogout() {
    localStorage.removeItem('genbi_token')
    setIsAuthenticated(false)
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />
  }

  return (
    <div className="app-container">
      <div className="bg-glow bg-glow-blue"></div>
      <div className="bg-glow bg-glow-purple"></div>

      <header className="app-header">
        <div className="logo-section">
          <Sparkles className="logo-icon text-glow" />
          <span className="logo-text">GenBI</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="status-badge">
            <Activity className="status-icon pulsate" />
            <span>Connecté</span>
          </div>
          <button
            onClick={handleLogout}
            className="sql-display__edit-btn"
            aria-label="Se déconnecter"
            title="Se déconnecter"
          >
            <LogOut size={14} />
          </button>
        </div>
      </header>

      <main className="chat-main">
        <ChatWindow />
      </main>
    </div>
  )
}

export default App
