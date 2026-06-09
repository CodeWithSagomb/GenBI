import { useState } from 'react'
import { Sparkles, Activity, LogOut, LayoutDashboard, MessageSquare } from 'lucide-react'
import { ChatWindow } from './components/chat/ChatWindow'
import { DashboardPage } from './components/dashboard/DashboardPage'
import { LoginPage } from './components/auth/LoginPage'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => !!localStorage.getItem('genbi_token')
  )
  const [page, setPage] = useState('dashboard')

  function handleLogout() {
    localStorage.removeItem('genbi_token')
    setIsAuthenticated(false)
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />
  }

  return (
    <div className="app-container">
      <div className="bg-glow bg-glow-blue" />
      <div className="bg-glow bg-glow-purple" />

      <header className="app-header">
        <div className="logo-section">
          <Sparkles className="logo-icon text-glow" />
          <span className="logo-text">GenBI</span>
        </div>

        {/* Navigation */}
        <nav className="app-nav">
          <button
            className={`app-nav__btn ${page === 'dashboard' ? 'app-nav__btn--active' : ''}`}
            onClick={() => setPage('dashboard')}
          >
            <LayoutDashboard size={15} />
            Dashboard
          </button>
          <button
            className={`app-nav__btn ${page === 'chat' ? 'app-nav__btn--active' : ''}`}
            onClick={() => setPage('chat')}
          >
            <MessageSquare size={15} />
            Chat
          </button>
        </nav>

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
        {page === 'dashboard' ? <DashboardPage /> : <ChatWindow />}
      </main>
    </div>
  )
}

export default App
