# Tasks — Phase 5 : RAG + Feedback Loop + JWT/RBAC

**Dernière mise à jour** : 2026-06-03
**Statut global** : 30 / 30 ✅ — T507/T530 exécutés et PASS dans Docker

---

## Track 1 — UX Conversation (Frontend)

### Infrastructure
- [x] **T501** — Refactoriser `useChat.js` : remplacer l'état plat par `messages[]`
- [x] **T502** — Refactoriser `ChatWindow.jsx` : boucle sur `messages[]`
- [x] **T503** — Créer `FeedbackButtons.jsx`
- [x] **T504** — Intégrer `FeedbackButtons` dans `ChatWindow`

### Tests Track 1
- [x] **T505** — Tests Vitest `useChat.test.js` (6 tests)
- [x] **T506** — Tests Vitest `FeedbackButtons.test.jsx` (5 tests)
- [x] **T507** — E2E Playwright : conversation multi-tours (`chat-flow.spec.js` — 2 tests PASS)

---

## Track 2 — RAG ChromaDB

### Infrastructure
- [x] **T508** — Mettre à jour `requirements.txt` (chromadb, python-jose, bcrypt)
- [x] **T509** — Volume ChromaDB dans `docker-compose.yml` + `data/chromadb/.gitkeep`
- [x] **T510** — Initialiser ChromaDB dans le lifespan FastAPI (`main.py`)

### Core RAG
- [x] **T511** — Créer `core/rag.py` (get_collection, index_example, retrieve_examples)
- [x] **T512** — 8 tests unitaires `tests/unit/test_rag.py`

### Intégration RAG dans le pipeline SQL
- [x] **T513** — `core/llm.py` : `build_sql_prompt(schema, question, examples=[])`
- [x] **T514** — `v1_sql_generation.txt` : bloc `{examples}` conditionnel
- [x] **T515** — `api/v1/chat/service.py` : retrieve_examples best-effort
- [x] **T516** — `api/v1/feedback/service.py` : index si `rating == 'good'`
- [x] **T517** — 5 tests intégration `tests/integration/test_rag_flow.py`

---

## Track 3 — JWT / RBAC

### Infrastructure
- [x] **T518** — Migration SQL `raw.users` (4 colonnes + 4 utilisateurs test)
- [x] **T519** — `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` dans `config.py`

### Core Security
- [x] **T520** — `core/security.py` (hash_password, verify_password, create/decode token)
- [x] **T521** — 10 tests unitaires `tests/unit/test_security.py`

### Endpoint Auth
- [x] **T522** — `api/v1/auth/` (login POST, refresh POST, me GET)
- [x] **T523** — 9 tests intégration `tests/integration/test_auth_jwt.py`

### Mise à jour Auth Existante
- [x] **T524** — `core/auth.py` : JWT (Bearer) + X-API-Key (dev compat)
- [x] **T525** — Router auth branché dans `main.py`

### Frontend JWT
- [x] **T526** — `src/components/auth/LoginPage.jsx`
- [x] **T527** — `src/services/api.js` : Bearer token + authApi.login + logout 401
- [x] **T528** — `src/App.jsx` : routing login/chat + bouton logout
- [x] **T529** — 4 tests Vitest `LoginPage.test.jsx`
- [x] **T530** — E2E Playwright flux login (`login-flow.spec.js` — 4 tests PASS)

---

## Récapitulatif

| Track | Tâches | Tests | Statut |
|---|---|---|---|
| Track 1 — UX Conversation | T501–T507 | Vitest + 2 E2E Playwright | ✅ |
| Track 2 — RAG ChromaDB | T508–T517 | 13 backend (8u+5i) | ✅ |
| Track 3 — JWT/RBAC | T518–T530 | 23 backend (10u+9i) + 4 frontend + 4 E2E | ✅ |
| **Stabilisation A1–A5** | fixes prod | 3 backend + 7 frontend + 6 E2E | ✅ |
| **Total** | **30 tâches** | **114 backend + 44 Vitest + 11 Playwright = 169** | **✅** |
