import { test, expect } from '@playwright/test'

// T530 — Flux login → chat + cas d'erreur

const LOGIN_OK = { access_token: 'tok_test_bourguiba', token_type: 'bearer' }
const SCHEMA_MOCK = { schema: 'SELECT * FROM marts.fct_sales' }

async function mockAuthRoutes(page) {
  await page.route('**/api/v1/auth/login', (r) =>
    r.fulfill({ status: 200, body: JSON.stringify(LOGIN_OK) })
  )
  await page.route('**/api/v1/schema', (r) =>
    r.fulfill({ status: 200, body: JSON.stringify(SCHEMA_MOCK) })
  )
}

test.describe('Flux login (T530)', () => {
  test.beforeEach(async ({ page }) => {
    // Réinitialise le localStorage avant chaque test
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
  })

  test('sans token → page login visible', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('button', { name: /connexion/i })).toBeVisible()
    await expect(page.getByLabelText(/email/i)).toBeVisible()
    await expect(page.getByLabelText(/mot de passe/i)).toBeVisible()
  })

  test('login réussi → accès au chat', async ({ page }) => {
    await mockAuthRoutes(page)
    await page.goto('/')

    await page.fill('[id="email"]', 'bourguiba@pharma.sn')
    await page.fill('[id="password"]', 'test123')
    await page.click('button[type="submit"]')

    // Après login → ChatWindow visible (input de question)
    await expect(page.locator('[data-testid="query-input"]')).toBeVisible({ timeout: 10000 })

    // Token stocké en localStorage
    const token = await page.evaluate(() => localStorage.getItem('genbi_token'))
    expect(token).toBe('tok_test_bourguiba')
  })

  test('mauvais credentials → message d\'erreur visible', async ({ page }) => {
    await page.route('**/api/v1/auth/login', (r) =>
      r.fulfill({ status: 401, body: JSON.stringify({ detail: 'Email ou mot de passe incorrect.' }) })
    )

    await page.goto('/')
    await page.fill('[id="email"]', 'inconnu@pharma.sn')
    await page.fill('[id="password"]', 'mauvais')
    await page.click('button[type="submit"]')

    await expect(page.locator('[role="alert"]')).toBeVisible({ timeout: 5000 })
    // Reste sur la page login
    await expect(page.getByRole('button', { name: /connexion/i })).toBeVisible()
  })

  test('token existant → chat directement sans login', async ({ page }) => {
    // Injecter un token valide avant le chargement
    await page.route('**/api/v1/schema', (r) =>
      r.fulfill({ status: 200, body: JSON.stringify(SCHEMA_MOCK) })
    )
    await page.addInitScript(() => {
      localStorage.setItem('genbi_token', 'tok_existant')
    })

    await page.goto('/')
    await expect(page.locator('[data-testid="query-input"]')).toBeVisible({ timeout: 10000 })
    await expect(page.getByRole('button', { name: /connexion/i })).not.toBeVisible()
  })
})
