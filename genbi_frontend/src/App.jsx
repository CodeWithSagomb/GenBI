import { Sparkles, Activity } from 'lucide-react'
import { ChatWindow } from './components/chat/ChatWindow'

function App() {
  return (
    <div className="app-container">
      <div className="bg-glow bg-glow-blue"></div>
      <div className="bg-glow bg-glow-purple"></div>

      <header className="app-header">
        <div className="logo-section">
          <Sparkles className="logo-icon text-glow" />
          <span className="logo-text">GenBI</span>
        </div>
        <div className="status-badge">
          <Activity className="status-icon pulsate" />
          <span>Pharmacie Bourguiba</span>
        </div>
      </header>

      <main className="chat-main">
        <ChatWindow />
      </main>
    </div>
  )
}

export default App
