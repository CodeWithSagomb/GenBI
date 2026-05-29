# GenBI — Tableau de Bord de Supervision

> Fichier de référence unique. Mettre à jour après chaque session de travail.

**Dernière mise à jour** : 2026-05-29
**Phase active** : Phase 3 — Backend API FastAPI

---

## État Global du Projet

```
Phase 1 ████████████████████ 100%  ✅ Infrastructure & Ingestion
Phase 2 ████████████████████ 100%  ✅ Couche Sémantique dbt
Phase 3 ░░░░░░░░░░░░░░░░░░░░   0%  🔄 Backend API FastAPI         ← ICI
Phase 4 ░░░░░░░░░░░░░░░░░░░░   0%  ⏳ Interface de Chat React
Phase 5 ░░░░░░░░░░░░░░░░░░░░   0%  ⏳ RAG & Feedback Loop
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

## Phase 3 — Backend API FastAPI 🔄 À DÉMARRER

**Prérequis** : `manifest.json` ✅ (Phase 2 terminée)
**Spec** : [specs/002-backend-api/spec.md](specs/002-backend-api/spec.md)
**Tasks** : [specs/002-backend-api/tasks.md](specs/002-backend-api/tasks.md) — **50 tâches · 46 cas de test**

| Module / Endpoint | Statut | Tests |
|---|---|---|
| Infrastructure tests + lifespan + exceptions | ⬜ | — |
| `core/sql_validator.py` | ⬜ | TDD — 13 cas 🔴 |
| `core/dbt_parser.py` | ⬜ | 6 cas unitaires |
| `core/llm.py` | ⬜ | 4 cas (prompt builder + timeout) |
| `core/database.py` (pool) | ⬜ | — |
| `GET /api/v1/schema` | ⬜ | 3 cas intégration |
| `POST /api/v1/chat` | ⬜ | 4 cas intégration |
| `POST /api/v1/execute` | ⬜ | 6 cas intégration 🔴 sécurité |
| `POST /api/v1/interpret` | ⬜ | 3 cas intégration |
| `POST /api/v1/query` ← endpoint principal | ⬜ | 4 cas intégration 🔴 |
| `GET /api/v1/suggestions` | ⬜ | 3 cas intégration |
| `POST /api/v1/feedback` | ⬜ | — |

---

## Phase 4 — Interface de Chat React ⏳ EN ATTENTE

**Prérequis** : Phases 2 + 3
**Spec** : [specs/003-frontend-chat/spec.md](specs/003-frontend-chat/spec.md)
**Tasks** : [specs/003-frontend-chat/tasks.md](specs/003-frontend-chat/tasks.md) — **33 tâches**

| Composant | Statut | Tests |
|---|---|---|
| `services/api.js` | ⬜ | — |
| `hooks/useChat.js` | ⬜ | 5 cas Vitest |
| `ChatWindow.jsx` | ⬜ | 5 cas Vitest |
| `SQLDisplay.jsx` | ⬜ | 5 cas Vitest |
| `DataTable.jsx` | ⬜ | 4 cas Vitest |
| `ChartRouter.jsx` | ⬜ | 5 cas Vitest |
| Flux chat complet | ⬜ | 3 scénarios Playwright E2E |

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
| III. Sécurité — `genbi_readonly` SELECT-only + TDD sur `sql_validator` | ✅ / ⏳ Phase 3 |
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
