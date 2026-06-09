import { useState } from 'react'
import { authApi } from '../../services/api'

export function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { access_token } = await authApi.login(email, password)
      localStorage.setItem('genbi_token', access_token)
      onLogin()
    } catch (err) {
      setError(err.message ?? 'Erreur de connexion.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-title">RuwaGenBI</h1>
        <p className="login-subtitle">Connectez-vous à votre pharmacie</p>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="vous@pharmacie.sn"
              required
              autoComplete="email"
              className="login-input"
            />
          </div>

          <div className="login-field">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
              className="login-input"
            />
          </div>

          {error && (
            <p role="alert" className="login-error">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="send-button login-submit"
          >
            {loading ? 'Connexion…' : 'Connexion'}
          </button>
        </form>
      </div>
    </div>
  )
}
