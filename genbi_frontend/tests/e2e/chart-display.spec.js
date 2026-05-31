import { test, expect } from '@playwright/test'

const SCHEMA_MOCK = { schema: 'SELECT * FROM marts.fct_sales' }

test.describe('Affichage graphiques', () => {
  test('une question sur les ventes par mois affiche un graphique en ligne', async ({ page }) => {
    await page.route('**/api/v1/schema', (r) => r.fulfill({ status: 200, body: JSON.stringify(SCHEMA_MOCK) }))
    await page.route('**/api/v1/chat', (r) =>
      r.fulfill({ status: 200, body: JSON.stringify({ sql: 'SELECT date, ca FROM marts.fct_sales', model_used: 'test' }) })
    )
    await page.route('**/api/v1/execute', (r) =>
      r.fulfill({
        status: 200,
        body: JSON.stringify({
          columns: ['date', 'ca'],
          rows: [['2026-02-01', 12000000], ['2026-03-01', 15000000], ['2026-04-01', 11000000]],
          row_count: 3,
          limit: 100,
          offset: 0,
        }),
      })
    )
    await page.route('**/api/v1/interpret', (r) =>
      r.fulfill({ status: 200, body: JSON.stringify({ insight: 'Tendance positive.' }) })
    )

    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    await page.fill('[data-testid="query-input"]', 'Ventes par mois depuis février 2026')
    await page.click('[data-testid="send-button"]')

    await page.waitForSelector('[data-testid="results-table"]', { timeout: 15000 })

    // Données avec colonne "date" → ChartRouter rend un LineChart
    await expect(page.locator('[data-chart-type="line"]')).toBeVisible()
    await expect(page.locator('[data-testid="results-table"]')).toBeVisible()
  })

  test('une question renvoyant 1 chiffre n\'affiche pas de graphique', async ({ page }) => {
    await page.route('**/api/v1/schema', (r) => r.fulfill({ status: 200, body: JSON.stringify(SCHEMA_MOCK) }))
    await page.route('**/api/v1/chat', (r) =>
      r.fulfill({ status: 200, body: JSON.stringify({ sql: 'SELECT COUNT(*) AS total FROM marts.fct_sales', model_used: 'test' }) })
    )
    await page.route('**/api/v1/execute', (r) =>
      r.fulfill({
        status: 200,
        body: JSON.stringify({ columns: ['total'], rows: [[1617]], row_count: 1, limit: 100, offset: 0 }),
      })
    )
    await page.route('**/api/v1/interpret', (r) =>
      r.fulfill({ status: 200, body: JSON.stringify({ insight: 'Vous avez 1617 ventes.' }) })
    )

    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    await page.fill('[data-testid="query-input"]', 'Combien de ventes ai-je ?')
    await page.click('[data-testid="send-button"]')

    await page.waitForSelector('[data-testid="results-table"]', { timeout: 15000 })

    // 1 seule ligne → ChartRouter retourne null → aucun graphique
    await expect(page.locator('[data-chart-type]')).not.toBeVisible()
    await expect(page.locator('[data-testid="results-table"]')).toBeVisible()
  })
})
