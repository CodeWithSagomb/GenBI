# GenBI — Tableau de Bord de Supervision

> Fichier de référence unique. Mettre à jour après chaque session de travail.

**Dernière mise à jour** : 2026-05-31
**Phase active** : Phase 5 — RAG ChromaDB + Feedback Loop

---

## État Global du Projet

```
Phase 1 ████████████████████ 100%  ✅ Infrastructure & Ingestion
Phase 2 ████████████████████ 100%  ✅ Couche Sémantique dbt
Phase 3 ████████████████████ 100%  ✅ Backend API FastAPI
Phase 4 ████████████████████ 100%  ✅ Interface de Chat React
Phase 5 ░░░░░░░░░░░░░░░░░░░░   0%  🔄 RAG & Feedback Loop          ← ICI
```

---

## Phase 1 — Infrastructure & Ingestion ✅ TERMINÉE

| Livrable | Statut |
|---|---|
| 6 services Docker (postgres, airflow, metabase, backend, frontend) | ✅ Up & healthy |
| Schémas PostgreSQL : `raw` / `staging` / `marts` | ✅ |
| User `genbi_readonly` + droits SELECT sur les 3 schémas | ✅ |
| DAG `ingest_pharmacy_data` — 10 tables raw | ✅ |
| **30 produits** · 16 classes thérapeutiques (antipaludéens inclus) | ✅ |
| **4 716 ventes** + 11 604 lignes · Fév–Mai 2026 (116 jours) | ✅ |
| 61 lots stocks · 200 ruptures · 30 retours grossistes | ✅ |
| CA total : **45 201 400 FCFA** | ✅ |
| Ollama natif : `qwen2.5-coder:7b` + `nomic-embed-text` | ✅ |

> Audit complet : [audit_phase1.md](audit_phase1.md)

---

## Phase 2 — Couche Sémantique dbt ✅ TERMINÉE

**Spec** : [specs/001-dbt-semantic-layer/spec.md](specs/001-dbt-semantic-layer/spec.md)

| Livrable | Statut |
|---|---|
| dbt-postgres 1.10.0 installé + `dbt debug` vert | ✅ |
| 10 sources raw déclarées | ✅ |
| 10 modèles staging (views dans `staging.*`) | ✅ |
| 5 dimensions + 4 tables de faits (tables dans `marts.*`) | ✅ |
| 149 colonnes documentées — 100% | ✅ |
| `dbt test` : **PASS=149 ERROR=0** | ✅ |
| `manifest.json` généré (1.0 MB) | ✅ |

**Modèles créés (19 total)**

| Staging (views) | Marts Dimensions | Marts Faits |
|---|---|---|
| `stg_raw__sales` ✅ | `dim_products` ✅ | `fct_sales` ✅ |
| `stg_raw__sale_details` ✅ | `dim_clients` ✅ | `fct_purchases` ✅ |
| `stg_raw__products` ✅ | `dim_pharmacies` ✅ | `fct_missed_sales` ✅ |
| `stg_raw__clients` ✅ | `dim_insurers` ✅ | `fct_wholesaler_returns` ✅ |
| `stg_raw__pharmacies` ✅ | `dim_stocks` ✅ | |
| `stg_raw__insurers` ✅ | | |
| `stg_raw__stocks` ✅ | | |
| `stg_raw__purchases` ✅ | | |
| `stg_raw__missed_sales` ✅ | | |
| `stg_raw__wholesaler_returns` ✅ | | |

---

## Phase 3 — Backend API FastAPI ✅ TERMINÉE

**Validé** : 2026-05-31 · **59/59 tests PASS** en 1.11s
**Spec** : [specs/002-backend-api/spec.md](specs/002-backend-api/spec.md)
**Tasks** : [specs/002-backend-api/tasks.md](specs/002-backend-api/tasks.md)

**Déploiement** : Scénario B — instance unique, 3 pharmacies, isolation via PostgreSQL RLS

| Module / Endpoint | Statut | Tests |
|---|---|---|
| Socle : lifespan + exceptions + middleware + RLS | ✅ | — |
| `core/auth.py` — API Key → pharmacy_id + rate limit | ✅ | 5 cas ✅ |
| `core/sql_validator.py` — TDD | ✅ | 13 cas ✅ |
| `core/dbt_parser.py` | ✅ | 6 cas ✅ |
| `core/llm.py` — asyncio.wait_for + prompts versionnés | ✅ | 4 cas ✅ |
| `core/database.py` — pool readonly + pool write + RLS setter | ✅ | — |
| `GET /api/v1/schema` | ✅ | 4 cas ✅ |
| `POST /api/v1/chat` | ✅ | 4 cas ✅ |
| `POST /api/v1/execute` — paginé + RLS vérifié | ✅ | 7 cas ✅ |
| `POST /api/v1/interpret` | ✅ | 3 cas ✅ |
| `POST /api/v1/query` ← pipeline complet | ✅ | 5 cas ✅ |
| `GET /api/v1/suggestions` | ✅ | 3 cas ✅ |
| `POST /api/v1/feedback` — genbi_write (INSERT+SELECT RETURNING) | ✅ | 5 cas ✅ |
| `GET /api/health` — enrichi (db+ollama+rls+manifest) | ✅ | — |

**Isolation RLS validée E2E** : Bourguiba 1 617 ventes · Almadies 1 530 ventes · Nation isolée ✅
**X-Request-ID** : UUID dans chaque réponse ✅ · Logs JSON structurés ✅

**Gotcha découvert** : PostgreSQL `RETURNING` requiert SELECT — `GRANT INSERT,SELECT ON raw.feedback` (pas INSERT seul).

---

## Phase 4 — Interface de Chat React ✅ TERMINÉE

**Validé** : 2026-05-31 · **26/26 Vitest PASS · 5/5 Playwright E2E PASS**
**Spec** : [specs/003-frontend-chat/spec.md](specs/003-frontend-chat/spec.md)
**Tasks** : [specs/003-frontend-chat/tasks.md](specs/003-frontend-chat/tasks.md) — 33/33 ✅

| Composant | Statut | Tests |
|---|---|---|
| `services/api.js` | ✅ | — |
| `hooks/useChat.js` | ✅ | 5 cas ✅ |
| `hooks/useSchema.js` | ✅ | — |
| `ChatWindow.jsx` | ✅ | 5 cas ✅ |
| `SQLDisplay.jsx` | ✅ | 5 cas ✅ |
| `DataTable.jsx` | ✅ | 4 cas ✅ |
| `ChartRouter.jsx` | ✅ | 5 cas ✅ |
| Flux chat complet | ✅ | 3 scénarios Playwright ✅ |
| Affichage graphique | ✅ | 2 scénarios Playwright ✅ |

**Gotchas découverts Phase 4 :**
- Alpine ARM64 : `npx playwright install` → binaire glibc incompatible → `apk add chromium` + `launchOptions.executablePath`
- `toLocaleString('fr-FR')` Node 20 → ` ` (espace insécable) → formateur regex avec espace ASCII
- Vitest ramasse `tests/e2e/` → exclure explicitement dans `vite.config.js`

---

## Phase 5 — RAG & Feedback Loop ⏳ BACKLOG

**Spec** : [specs/004-rag-feedback/spec.md](specs/004-rag-feedback/spec.md)
**Tasks** : À créer après Phase 4

---

## Services & Connectivité

| Service | Port | Statut actuel |
|---|---|---|
| PostgreSQL | 5432 | ✅ healthy |
| Airflow | 8080 | ✅ healthy → http://localhost:8080 |
| Metabase | 3000 | ✅ up → http://localhost:3000 |
| Ollama (natif) | 11434 | ✅ 2 modèles |
| Backend FastAPI | 8000 | ✅ healthy → http://localhost:8000/api/health |
| Frontend React | 5173 | ✅ up → http://localhost:5173 |

---

## Blocages Actifs

| # | Blocage | Impact | Action |
|---|---|---|---|
| ~~B1~~ | ~~`dbt` non installé~~ | ~~🔴~~ | ✅ Résolu — dbt 1.10.0 |
| ~~B2~~ | ~~`manifest.json` absent~~ | ~~🔴~~ | ✅ Résolu — 1.0 MB généré |

---

## Constitution — Conformité

| Principe | Statut |
|---|---|
| I. Souveraineté des données — LLM local, 0 appel externe | ✅ |
| II. Sémantique-First — manifest.json comme seule source du prompt | ⏳ Phase 2 |
| III. Sécurité — `genbi_readonly` SELECT-only + TDD `sql_validator` + RLS PostgreSQL | ✅ |
| IV. Open-Source & Vendor-Agnostic | ✅ |
| V. Simplicité incrémentale — MVP par user story | ✅ |

---

## Références

| Document | Rôle |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Contexte auto-chargé par Claude Code |
| [.specify/memory/constitution.md](.specify/memory/constitution.md) | 5 principes non-négociables |
| [guide_meilleures_pratiques.md](guide_meilleures_pratiques.md) | Standards techniques par couche |
| [formation_claude_code.md](formation_claude_code.md) | Harness Claude Code — configuration |
| [formation_spec_kit.md](formation_spec_kit.md) | Méthode SDD (spec → plan → tasks → implement) |
| [audit_phase1.md](audit_phase1.md) | Audit complet Phase 1 |
| [vision_et_objectifs.md](vision_et_objectifs.md) | Vision produit & feuille de route |
| [exploration_donnees_pharmaceutiques.md](exploration_donnees_pharmaceutiques.md) | Contexte métier pharma Dakar |
