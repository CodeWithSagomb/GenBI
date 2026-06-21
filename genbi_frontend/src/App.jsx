import { useState, useEffect } from 'react'
import { Sparkles, Activity, LogOut, LayoutDashboard, MessageSquare, Sun, Moon, User, Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { ChatWindow } from './components/chat/ChatWindow'
import { DashboardPage } from './components/dashboard/DashboardPage'
import { LoginPage } from './components/auth/LoginPage'
import { ProfilePage } from './components/profile/ProfilePage'
import { ToastProvider } from './hooks/useToast'
import { LanguageProvider, useLang } from './i18n/LanguageContext'
import './i18n/index'

function AppInner() {
  const { t } = useTranslation()
  const { lang, toggleLang } = useLang()
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
    <ToastProvider>
    <div className="app-container">
      <div className="bg-glow bg-glow-blue" />
      <div className="bg-glow bg-glow-purple" />

      <header className="app-header">
        <div className="logo-section">
          <Sparkles className="logo-icon text-glow" />
          <span className="logo-text">{t('app.logo')}</span>
        </div>

        <nav className="app-nav">
          <button
            className={`app-nav__btn ${page === 'dashboard' ? 'app-nav__btn--active' : ''}`}
            onClick={() => setPage('dashboard')}
          >
            <LayoutDashboard size={15} />
            {t('app.nav_dashboard')}
          </button>
          <button
            className={`app-nav__btn ${page === 'chat' ? 'app-nav__btn--active' : ''}`}
            onClick={() => setPage('chat')}
          >
            <MessageSquare size={15} />
            {t('app.nav_chat')}
          </button>
          <button
            className={`app-nav__btn ${page === 'profile' ? 'app-nav__btn--active' : ''}`}
            onClick={() => setPage('profile')}
          >
            <User size={15} />
            {t('app.nav_profile')}
          </button>
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="status-badge">
            <Activity className="status-icon pulsate" />
            <span>{t('app.status_connected')}</span>
          </div>
          <button
            onClick={toggleLang}
            className="theme-toggle"
            aria-label={t('app.toggle_theme')}
            title={lang === 'fr' ? 'Switch to English' : 'Passer en français'}
          >
            <Languages size={15} />
            <span style={{ fontSize: '0.7rem', fontWeight: 700, marginLeft: '2px' }}>
              {lang === 'fr' ? 'FR' : 'EN'}
            </span>
          </button>
          <button
            onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
            className="theme-toggle"
            aria-label={t('app.toggle_theme')}
            title={theme === 'dark' ? t('app.theme_day') : t('app.theme_night')}
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>
          <button
            onClick={handleLogout}
            className="sql-display__edit-btn"
            aria-label={t('app.logout')}
            title={t('app.logout')}
          >
            <LogOut size={14} />
          </button>
        </div>
      </header>

      <main className={`chat-main${page === 'dashboard' ? ' chat-main--dashboard' : ''}`}>
        <div className={`page-view${page === 'dashboard' ? ' page-view--active' : ''}`}>
          <DashboardPage />
        </div>
        <div className={`page-view${page === 'chat' ? ' page-view--active' : ''}`}>
          <ChatWindow />
        </div>
        <div className={`page-view${page === 'profile' ? ' page-view--active' : ''}`}>
          <ProfilePage onLogout={handleLogout} />
        </div>
      </main>
    </div>
    </ToastProvider>
  )
}

function App() {
  return (
    <LanguageProvider>
      <AppInner />
    </LanguageProvider>
  )
}

export default App
