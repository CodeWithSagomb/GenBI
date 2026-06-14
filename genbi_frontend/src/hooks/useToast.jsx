import { createContext, useContext, useState, useCallback } from 'react'
import { CheckCircle, AlertCircle } from 'lucide-react'

const ToastCtx = createContext(null)

function ToastContainer({ toasts }) {
  if (!toasts.length) return null
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast--${t.type}`}>
          {t.type === 'error' ? <AlertCircle size={14} /> : <CheckCircle size={14} />}
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  )
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const show = useCallback((message, type = 'success') => {
    const id = Math.random().toString(36).slice(2)
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000)
  }, [])

  return (
    <ToastCtx.Provider value={show}>
      {children}
      <ToastContainer toasts={toasts} />
    </ToastCtx.Provider>
  )
}

export const useToast = () => useContext(ToastCtx)
