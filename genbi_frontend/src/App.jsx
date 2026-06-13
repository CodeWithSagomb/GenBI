import { useState, useEffect } from 'react'
import { Sparkles, Activity, LogOut, LayoutDashboard, MessageSquare, Sun, Moon } from 'lucide-react'
import { ChatWindow } from './components/chat/ChatWindow'
import { DashboardPage } from './components/dashboard/DashboardPage'
import { LoginPage } from './components/auth/LoginPage'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => !!localStorage.getItem('genbi_token')
  )
  const [page, setPage] = useState('dashboard')
  const [theme, setTheme] = useState(() => localStorage.getItem('genbi_theme') || 'dark')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('genbi_theme', theme)
  }, [theme])

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
          <span className="logo-text">RuwaGenBI</span>
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
            onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
            className="theme-toggle"
            aria-label="Changer le thème"
            title={theme === 'dark' ? 'Mode jour' : 'Mode nuit'}
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>
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

      <main className={`chat-main${page === 'dashboard' ? ' chat-main--dashboard' : ''}`}>
        <div style={{ display: page === 'dashboard' ? 'contents' : 'none' }}><DashboardPage /></div>
        <div style={{ display: page === 'chat' ? 'contents' : 'none' }}><ChatWindow /></div>
      </main>
    </div>
  )
}

export default App
