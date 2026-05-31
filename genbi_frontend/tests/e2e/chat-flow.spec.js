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

// Helpers partagés pour les tests multi-tours
const EXECUTE_MOCK_1 = { columns: ['ca'], rows: [[15000000]], row_count: 1, limit: 100, offset: 0 }
const EXECUTE_MOCK_2 = { columns: ['produit', 'total'], rows: [['Paracétamol', 500]], row_count: 1, limit: 100, offset: 0 }

async function mockMultiTurnRoutes(page) {
  await page.route('**/api/v1/schema', (r) => r.fulfill({ status: 200, body: JSON.stringify(SCHEMA_MOCK) }))
  await page.route('**/api/v1/interpret', (r) => r.fulfill({ status: 200, body: JSON.stringify(INTERPRET_MOCK) }))

  let chatCall = 0
  await page.route('**/api/v1/chat', (r) => {
    chatCall++
    const sql = chatCall === 1
      ? 'SELECT SUM(ca) AS ca FROM marts.fct_sales'
      : 'SELECT produit, total FROM marts.fct_top_produits'
    r.fulfill({ status: 200, body: JSON.stringify({ sql }) })
  })

  let executeCall = 0
  await page.route('**/api/v1/execute', (r) => {
    executeCall++
    r.fulfill({ status: 200, body: JSON.stringify(executeCall === 1 ? EXECUTE_MOCK_1 : EXECUTE_MOCK_2) })
  })
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

// T507 — Conversation multi-tours + feedback
test.describe('Conversation multi-tours + feedback', () => {
  test('deux questions affichent deux échanges simultanément', async ({ page }) => {
    await mockMultiTurnRoutes(page)
    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    await page.fill('[data-testid="query-input"]', 'Mon CA total ?')
    await page.click('[data-testid="send-button"]')
    await page.waitForSelector('[data-testid="results-table"]', { timeout: 15000 })

    await page.fill('[data-testid="query-input"]', 'Mes top produits ?')
    await page.click('[data-testid="send-button"]')

    await expect(page.locator('[data-testid="results-table"]')).toHaveCount(2, { timeout: 15000 })
    await expect(page.getByText('Mon CA total ?')).toBeVisible()
    await expect(page.getByText('Mes top produits ?')).toBeVisible()
  })

  test('clic 👍 sur la première réponse désactive ses boutons sans affecter la seconde', async ({ page }) => {
    let feedbackBody = null
    await page.route('**/api/v1/feedback', (r) => {
      feedbackBody = r.request().postDataJSON()
      r.fulfill({ status: 200, body: JSON.stringify({ status: 'ok' }) })
    })
    await mockMultiTurnRoutes(page)
    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    await page.fill('[data-testid="query-input"]', 'Mon CA total ?')
    await page.click('[data-testid="send-button"]')
    await page.waitForSelector('[data-testid="results-table"]', { timeout: 15000 })

    await page.fill('[data-testid="query-input"]', 'Mes top produits ?')
    await page.click('[data-testid="send-button"]')
    await expect(page.locator('[data-testid="results-table"]')).toHaveCount(2, { timeout: 15000 })

    const groups = page.locator('.feedback-buttons')
    await groups.first().getByRole('button', { name: /👍/ }).click()

    await expect(groups.first().getByRole('button', { name: /👍/ })).toBeDisabled()
    await expect(groups.first().getByRole('button', { name: /👎/ })).toBeDisabled()
    await expect(groups.first().getByText(/merci/i)).toBeVisible()

    await expect(groups.nth(1).getByRole('button', { name: /👍/ })).toBeEnabled()
    await expect(groups.nth(1).getByRole('button', { name: /👎/ })).toBeEnabled()

    expect(feedbackBody).not.toBeNull()
    expect(feedbackBody.rating).toBe('good')
  })
})
