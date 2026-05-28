# Tasks : 003-frontend-chat

**Input** : `specs/003-frontend-chat/spec.md`
**Constitution** : `.specify/memory/constitution.md`
**Prérequis** : Phases 2 + 3 opérationnelles (backend `/chat` et `/execute` répondent)

---

## Stratégie de test

**Deux niveaux :**
1. **Tests de composants** (Vitest + React Testing Library) — testent la logique et le rendu sans navigateur
2. **Tests E2E** (Playwright) — testent le flux complet utilisateur dans un vrai navigateur

**Règle :** les tests de composants sont écrits **avec** l'implémentation. Les tests E2E couvrent les user stories P1 et P2 **après** que les composants sont en place.

```
genbi_frontend/
├── src/
│   ├── components/...
│   └── hooks/...
├── tests/
│   ├── unit/
│   │   ├── ChatWindow.test.jsx
│   │   ├── SQLDisplay.test.jsx
│   │   ├── ChartRouter.test.jsx
│   │   └── useChat.test.js
│   └── e2e/
│       ├── chat-flow.spec.js      ← US1 : poser une question et voir les résultats
│       └── chart-display.spec.js  ← US2 : visualisation graphique
```

**Commandes :**
```bash
npm run test          # Vitest — tests unitaires composants
npm run test:e2e      # Playwright — tests E2E
```

---

## Format : `[ID] [P?] [US?] Description`

---

## Phase 1 : Setup infrastructure de test

- [ ] T001 Installer les dépendances de test :
  ```bash
  npm install -D vitest @vitest/ui jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
  npm install -D @playwright/test
  npx playwright install chromium
  ```
- [ ] T002 Configurer Vitest dans `vite.config.js` :
  ```js
  test: { environment: 'jsdom', setupFiles: ['./tests/setup.js'] }
  ```
- [ ] T003 Créer `tests/setup.js` — import `@testing-library/jest-dom`
- [ ] T004 Ajouter scripts dans `package.json` :
  ```json
  "test": "vitest run",
  "test:watch": "vitest",
  "test:e2e": "playwright test"
  ```
- [ ] T005 Créer `playwright.config.js` — baseURL: `http://localhost:5173`, browser: chromium
- [ ] T006 Valider : `npm run test -- --reporter=verbose` — collecte sans erreur

**Checkpoint** : infrastructure de test en place

---

## Phase 2 : Structure des composants

- [ ] T007 [P] Créer `src/services/api.js` — client HTTP centralisé (chatApi.sendQuestion, chatApi.executeSQL, chatApi.getSchema)
- [ ] T008 [P] Créer `src/hooks/useChat.js` — state machine : idle → loading → success/error
- [ ] T009 [P] Créer `src/hooks/useSchema.js` — fetch du schéma au démarrage

---

## Phase 3 : User Story 1 — Chat & Résultats 🎯 MVP

### Tests composants (écrire avec l'implémentation)

- [ ] T010 [T] [US1] Créer `tests/unit/useChat.test.js` :
  ```js
  test_state_initial_est_idle()
  test_sendQuestion_passe_en_loading()
  test_sendQuestion_succes_stocke_sql_et_resultats()
  test_sendQuestion_erreur_stocke_message_erreur()
  test_question_vide_ne_declenche_pas_appel_api()
  ```
- [ ] T011 [T] [US1] Créer `tests/unit/SQLDisplay.test.jsx` :
  ```js
  test_affiche_le_sql_recu()
  test_sql_est_dans_un_element_pre()   // accessibilité copier/coller
  test_affiche_rien_si_sql_null()
  ```
- [ ] T012 [T] [US1] Créer `tests/unit/ChatWindow.test.jsx` :
  ```js
  test_input_vide_au_demarrage()
  test_submit_avec_question_appelle_hook()
  test_affiche_loading_pendant_requete()
  test_affiche_erreur_si_api_echoue()
  test_affiche_resultats_apres_succes()
  ```

### Implémentation US1

- [ ] T013 [US1] Créer `src/components/chat/QueryInput.jsx` — champ texte + bouton Envoyer + gestion Enter
- [ ] T014 [US1] Créer `src/components/chat/MessageBubble.jsx` — bulle user / bulle IA avec état
- [ ] T015 [US1] Créer `src/components/chat/SQLDisplay.jsx` — bloc SQL avec fond sombre
- [ ] T016 [US1] Créer `src/components/data/DataTable.jsx` — tableau générique colonnes/lignes depuis JSON
- [ ] T017 [US1] Créer `src/components/chat/ChatWindow.jsx` — assemblage + appels `useChat`
- [ ] T018 Mettre à jour `App.jsx` — remplacer la page vitrine par `ChatWindow`
- [ ] T019 Exécuter `npm run test` — cible : **0 échec**

**Checkpoint US1** : `npm run test` vert. Tester manuellement : poser une question → voir le SQL et le tableau.

---

## Phase 4 : User Story 2 — Visualisations Recharts

### Tests composants

- [ ] T020 [T] [US2] Créer `tests/unit/ChartRouter.test.jsx` :
  ```js
  test_retourne_LineChart_pour_donnees_temporelles()   // colonne date + montant
  test_retourne_BarChart_pour_categories()             // colonne nom + valeur
  test_retourne_null_pour_valeur_unique()              // 1 seule ligne
  test_retourne_null_pour_donnees_vides()
  test_detecte_colonne_date_correctement()
  ```
- [ ] T021 [T] [US2] Créer `tests/unit/DataTable.test.jsx` :
  ```js
  test_affiche_les_colonnes()
  test_affiche_les_lignes()
  test_formate_montants_fcfa_avec_separateurs()
  test_tableau_vide_affiche_message()
  ```

### Implémentation US2

- [ ] T022 [US2] Créer `src/components/visualizations/ChartRouter.jsx` — logique de sélection auto (LineChart si colonne date, BarChart si catégories, null si 1 valeur)
- [ ] T023 [P] [US2] Créer `src/components/visualizations/SalesLineChart.jsx` — Recharts `<LineChart>` responsive
- [ ] T024 [P] [US2] Créer `src/components/visualizations/RankingBarChart.jsx` — Recharts `<BarChart>` horizontal
- [ ] T025 Intégrer `ChartRouter` dans `ChatWindow` sous le `DataTable`
- [ ] T026 Exécuter `npm run test` — 0 échec

**Checkpoint US2** : graphiques auto-générés selon le type de données.

---

## Phase 5 : User Story 3 — Correction SQL

- [ ] T027 [T] [US3] Créer `tests/unit/SQLDisplay.test.jsx` — ajouter :
  ```js
  test_bouton_modifier_visible()
  test_clic_modifier_ouvre_editeur()
  test_reexecution_appelle_execute_avec_nouveau_sql()
  ```
- [ ] T028 [US3] Étendre `SQLDisplay.jsx` — mode édition avec `<textarea>` + bouton "Ré-exécuter"
- [ ] T029 Exécuter `npm run test` — 0 échec

---

## Phase 6 : Tests E2E Playwright

- [ ] T030 [T] [US1] Créer `tests/e2e/chat-flow.spec.js` :
  ```js
  test('poser une question et voir les résultats', async ({ page }) => {
    await page.goto('/')
    await page.fill('[data-testid="query-input"]', 'Quel est le CA de Mars 2026 ?')
    await page.click('[data-testid="send-button"]')
    await page.waitForSelector('[data-testid="sql-display"]', { timeout: 30000 })
    await expect(page.locator('[data-testid="results-table"]')).toBeVisible()
  })
  test('une erreur API affiche un message lisible')
  test('une question vide ne déclenche pas de requête')
  ```
- [ ] T031 [T] [US2] Créer `tests/e2e/chart-display.spec.js` :
  ```js
  test('une question sur les ventes par mois affiche un graphique')
  test('une question renvoyant 1 chiffre n'affiche pas de graphique')
  ```
- [ ] T032 Ajouter les attributs `data-testid` sur les éléments ciblés par Playwright (QueryInput, SendButton, SQLDisplay, ResultsTable)
- [ ] T033 Exécuter `npm run test:e2e` — cible : **0 échec**

**Checkpoint Final** : `npm run test` + `npm run test:e2e` → 100% vert

---

## Couverture de test cible

| Module | Type | Cas testés | Priorité |
|---|---|---|---|
| `useChat.js` | Unitaire | 5 cas | 🟡 Important |
| `SQLDisplay.jsx` | Unitaire | 5 cas | 🟡 Important |
| `ChatWindow.jsx` | Unitaire | 5 cas | 🟡 Important |
| `ChartRouter.jsx` | Unitaire | 5 cas | 🟡 Important |
| `DataTable.jsx` | Unitaire | 4 cas | 🟢 Standard |
| Flux chat complet | E2E | 3 scénarios | 🔴 Critique |
| Affichage graphique | E2E | 2 scénarios | 🟡 Important |
