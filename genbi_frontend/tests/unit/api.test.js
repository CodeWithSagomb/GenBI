/**
 * Tests unitaires pour src/services/api.js
 * Vérifie le comportement sur 401 (logout) et 403 (pas de logout).
 */
import { vi, describe, test, expect, beforeEach } from 'vitest'

// On importe le module après avoir injecté fetch
let chatApi
let authHeaders

beforeEach(async () => {
  vi.resetModules()
  localStorage.clear()
  // Réimporte le module frais pour chaque test (localStorage potentiellement différent)
  const mod = await import('../../src/services/api?t=' + Date.now())
  chatApi = mod.chatApi
})

describe('api.js — gestion des erreurs HTTP', () => {
  test('401 supprime le token localStorage et lève "Session expirée"', async () => {
    localStorage.setItem('genbi_token', 'tok_valide')
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Token expiré.' }),
    })

    const mod = await import('../../src/services/api?t=' + Date.now())
    await expect(mod.chatApi.getSchema()).rejects.toThrow('Session expirée')
    expect(localStorage.getItem('genbi_token')).toBeNull()
  })

  test('403 NE supprime PAS le token et lève le message d\'erreur API', async () => {
    localStorage.setItem('genbi_token', 'tok_admin')
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ error: 'Accès réservé aux pharmaciens.' }),
    })

    const mod = await import('../../src/services/api?t=' + Date.now())
    await expect(mod.chatApi.getSchema()).rejects.toThrow('Accès réservé aux pharmaciens.')
    // Token préservé — l'utilisateur reste connecté
    expect(localStorage.getItem('genbi_token')).toBe('tok_admin')
  })

  test('500 lève le message d\'erreur sans toucher au token', async () => {
    localStorage.setItem('genbi_token', 'tok_ok')
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ error: 'Erreur serveur.' }),
    })

    const mod = await import('../../src/services/api?t=' + Date.now())
    await expect(mod.chatApi.getSchema()).rejects.toThrow('Erreur serveur.')
    expect(localStorage.getItem('genbi_token')).toBe('tok_ok')
  })
})
