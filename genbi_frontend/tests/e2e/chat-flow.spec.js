import { test, expect } from '@playwright/test'

// Mock du schéma appelé au montage de ChatWindow (évite le blocage networkidle)
const SCHEMA_MOCK = { schema: 'SELECT * FROM marts.fct_sales' }
const CHAT_MOCK = { sql: 'SELECT SUM(total_amount) AS ca FROM marts.fct_sales', model_used: 'test' }
const EXECUTE_MOCK = {
  columns: ['mois', 'ca'],
  rows: [['2026-03', 15000000], ['2026-04', 12000000]],
  row_count: 2,
  limit: 100,
  offset: 0,
}
const INTERPRET_MOCK = { insight: 'Votre CA est en bonne progression.' }

async function mockAllRoutes(page) {
  await page.route('**/api/v1/schema', (r) => r.fulfill({ status: 200, body: JSON.stringify(SCHEMA_MOCK) }))
  await page.route('**/api/v1/chat', (r) => r.fulfill({ status: 200, body: JSON.stringify(CHAT_MOCK) }))
  await page.route('**/api/v1/execute', (r) => r.fulfill({ status: 200, body: JSON.stringify(EXECUTE_MOCK) }))
  await page.route('**/api/v1/interpret', (r) => r.fulfill({ status: 200, body: JSON.stringify(INTERPRET_MOCK) }))
}

test.describe('Flux chat complet', () => {
  test('poser une question et voir les résultats', async ({ page }) => {
    await mockAllRoutes(page)
    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    await page.fill('[data-testid="query-input"]', 'Quel est le chiffre d\'affaires de mars 2026 ?')
    await page.click('[data-testid="send-button"]')

    await page.waitForSelector('[data-testid="sql-display"]', { timeout: 15000 })
    await expect(page.locator('[data-testid="results-table"]')).toBeVisible()
  })

  test('une erreur API affiche un message lisible', async ({ page }) => {
    await page.route('**/api/v1/schema', (r) => r.fulfill({ status: 200, body: JSON.stringify(SCHEMA_MOCK) }))
    await page.route('**/api/v1/chat', (r) =>
      r.fulfill({ status: 500, body: JSON.stringify({ detail: 'Erreur serveur simulée' }) })
    )

    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    await page.fill('[data-testid="query-input"]', 'Question test erreur')
    await page.click('[data-testid="send-button"]')

    await expect(page.locator('.chat-error')).toBeVisible({ timeout: 10000 })
  })

  test('une question vide ne déclenche pas de requête', async ({ page }) => {
    await page.route('**/api/v1/schema', (r) => r.fulfill({ status: 200, body: JSON.stringify(SCHEMA_MOCK) }))

    let chatCalled = false
    await page.route('**/api/v1/chat', (r) => { chatCalled = true; r.fulfill({ status: 200, body: '{}' }) })

    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    // Pression Enter sur input vide (bouton disabled, on passe par le clavier)
    await page.press('[data-testid="query-input"]', 'Enter')
    await page.waitForTimeout(500)

    expect(chatCalled).toBe(false)
    await expect(page.locator('[data-testid="loading-indicator"]')).not.toBeVisible()
  })
})
