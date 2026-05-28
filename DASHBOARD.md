# GenBI — Tableau de Bord de Supervision

> Fichier de référence unique pour suivre l'état du projet en temps réel.
> Mettre à jour ce fichier après chaque session de travail.

**Dernière mise à jour** : 2026-05-28
**Phase active** : Phase 2 — Couche Sémantique dbt

---

## État Global du Projet

```
Phase 1 ████████████████████ 100%  ✅ Infrastructure & Ingestion
Phase 2 ░░░░░░░░░░░░░░░░░░░░   0%  🔄 Couche Sémantique dbt      ← ICI
Phase 3 ░░░░░░░░░░░░░░░░░░░░   0%  ⏳ Backend API FastAPI
Phase 4 ░░░░░░░░░░░░░░░░░░░░   0%  ⏳ Interface de Chat React
Phase 5 ░░░░░░░░░░░░░░░░░░░░   0%  ⏳ RAG & Feedback Loop
```

> Audit Phase 1 validé le 2026-05-28 — voir [audit_phase1.md](audit_phase1.md)

---

## Phase 1 — Infrastructure & Ingestion ✅ TERMINÉE

**Objectif** : Environnement Docker + pipeline d'ingestion pharmacie opérationnel.

| Livrable | Statut | Fichier |
|---|---|---|
| docker-compose.yml (8 services) | ✅ | [docker-compose.yml](docker-compose.yml) |
| init.sql (schémas + user read-only) | ✅ | [data/postgres-init/init.sql](data/postgres-init/init.sql) |
| DAG `ingest_pharmacy_data` | ✅ exécuté avec succès | [airflow/dags/ingest_pharmacy_data.py](airflow/dags/ingest_pharmacy_data.py) |
| 10 tables `raw.*` créées | ✅ 10/10 tables | Vérifié en base |
| 3 614 ventes + 9 062 lignes (Mars–Mai 2026) | ✅ | CA total : 47 837 250 FCFA |
| Makefile (commandes up/down/clean) | ✅ | [Makefile](Makefile) |
| Ollama `qwen2.5-coder:7b` | ✅ téléchargé | `ollama list` |
| Ollama `nomic-embed-text` | ✅ téléchargé (bonus Phase 5) | `ollama list` |
| `genbi_readonly` SELECT sur raw.* | ✅ vérifié | ALTER DEFAULT PRIVILEGES actif |

**Pour vérifier** : `make ps` → tous les conteneurs sont `Up`

---

## Phase 2 — Couche Sémantique dbt 🔄 EN COURS (0 / 39 tâches)

**Objectif** : Transformer les données brutes en tables analytiques documentées pour l'IA.
**BLOQUANT** : Sans `manifest.json`, les Phases 3, 4 et 5 ne peuvent pas démarrer.

**Spec** : [specs/001-dbt-semantic-layer/spec.md](specs/001-dbt-semantic-layer/spec.md)
**Tasks** : [specs/001-dbt-semantic-layer/tasks.md](specs/001-dbt-semantic-layer/tasks.md)

### Progression par phase interne

| Phase interne | Tâches | Statut | Checkpoint |
|---|---|---|---|
| Setup dbt | T001–T004 | ⬜ 0/4 | `dbt debug` passe |
| Sources raw | T005–T006 | ⬜ 0/2 | Sources reconnues |
| Staging US1 & US2 | T007–T015 | ⬜ 0/9 | `dbt test` staging vert |
| Staging US3 | T016–T021 | ⬜ 0/6 | 10 modèles staging OK |
| Dimensions | T022–T026 | ⬜ 0/5 | 4 tables `dim_*` créées |
| Tables de faits | T027–T034 | ⬜ 0/8 | `dbt test` 100% vert |
| Manifest & Validation | T035–T039 | ⬜ 0/5 | `manifest.json` généré |

### Modèles à créer

**Staging (views)**
- [ ] `stg_raw__sales`
- [ ] `stg_raw__sale_details`
- [ ] `stg_raw__products`
- [ ] `stg_raw__clients`
- [ ] `stg_raw__pharmacies`
- [ ] `stg_raw__insurers`
- [ ] `stg_raw__stocks`
- [ ] `stg_raw__purchases`
- [ ] `stg_raw__missed_sales`
- [ ] `stg_raw__wholesaler_returns`

**Marts — Dimensions (tables)**
- [ ] `dim_products`
- [ ] `dim_clients`
- [ ] `dim_pharmacies`
- [ ] `dim_insurers`
- [ ] `dim_stocks`

**Marts — Faits (tables)**
- [ ] `fct_sales`
- [ ] `fct_purchases`
- [ ] `fct_missed_sales`
- [ ] `fct_wholesaler_returns`

**Artefact final**
- [ ] `dbt_project/target/manifest.json` généré

---

## Phase 3 — Backend API FastAPI ⏳ EN ATTENTE

**Prérequis** : `manifest.json` de la Phase 2
**Spec** : [specs/002-backend-api/spec.md](specs/002-backend-api/spec.md)
**Tasks** : À créer (`/speckit.tasks` sur la spec)

| Endpoint | Statut | Description |
|---|---|---|
| `GET /` | ✅ Existe | Page d'accueil (squelette) |
| `GET /api/health` | ✅ Existe | Health check basique |
| `GET /api/v1/schema` | ⬜ À faire | Liste tables + colonnes depuis manifest.json |
| `POST /api/v1/chat` | ⬜ À faire | Question → SQL via Ollama |
| `POST /api/v1/execute` | ⬜ À faire | SQL validé → résultats JSON |

**Modules à créer**
- [ ] `core/dbt_parser.py` — lecteur de manifest.json
- [ ] `core/llm.py` — client Ollama (LiteLLM)
- [ ] `core/sql_validator.py` — whitelist SELECT via SQLGlot
- [ ] `api/v1/chat/` — router + service + schemas
- [ ] `api/v1/execute/` — router + service + schemas
- [ ] `api/v1/schema/` — router + service

---

## Phase 4 — Interface de Chat React ⏳ EN ATTENTE

**Prérequis** : Phases 2 + 3 opérationnelles
**Spec** : [specs/003-frontend-chat/spec.md](specs/003-frontend-chat/spec.md)
**Tasks** : À créer

| Composant | Statut | Description |
|---|---|---|
| Design system CSS | ✅ Existe | Dark mode glassmorphism prêt |
| Page vitrine | ✅ Existe | `App.jsx` — page d'accueil |
| `ChatWindow.jsx` | ⬜ À faire | Conteneur principal |
| `MessageBubble.jsx` | ⬜ À faire | Bulle user / IA |
| `SQLDisplay.jsx` | ⬜ À faire | Affichage SQL avec highlighting |
| `QueryInput.jsx` | ⬜ À faire | Barre de saisie |
| `DataTable.jsx` | ⬜ À faire | Tableau de résultats |
| `ChartRouter.jsx` | ⬜ À faire | Sélection auto du graphique Recharts |
| `useChat.js` | ⬜ À faire | Hook logique chat + API |
| `services/api.js` | ⬜ À faire | Client HTTP centralisé |

---

## Phase 5 — RAG & Feedback Loop ⏳ BACKLOG

**Prérequis** : Phases 2 + 3 + 4 opérationnelles
**Spec** : [specs/004-rag-feedback/spec.md](specs/004-rag-feedback/spec.md)
**Tasks** : À créer (après Phase 4)

| Composant | Statut |
|---|---|
| ChromaDB initialisé | ⬜ |
| Pipeline embedding (nomic-embed-text) | ⬜ |
| Retrieval few-shot dans le prompt | ⬜ |
| Bouton "✅ Correct" dans le frontend | ⬜ |
| Éditeur SQL de correction | ⬜ |

---

## Services & Connectivité

Vérifier avec `make ps` avant chaque session de travail.

| Service | Port | URL de vérification |
|---|---|---|
| PostgreSQL | 5432 | `psql -h localhost -U postgres -d genbi` |
| Airflow UI | 8080 | http://localhost:8080 |
| Metabase | 3000 | http://localhost:3000 |
| Ollama (natif) | 11434 | `ollama list` |
| Backend FastAPI | 8000 | http://localhost:8000/api/health |
| Frontend React | 5173 | http://localhost:5173 |

---

## Constitution — Conformité

Les 5 principes non-négociables. Tout code mergé doit les respecter.

| Principe | Vérifié | Détail |
|---|---|---|
| I. Souveraineté des données | ✅ | Ollama local, pas d'appel externe |
| II. Sémantique-First | ⬜ Vérifier Phase 3 | Le prompt doit utiliser manifest.json |
| III. Sécurité par architecture | ✅ | `genbi_readonly` créé dans init.sql |
| IV. Open-Source & Vendor-Agnostic | ✅ | Toute la stack est open-source |
| V. Simplicité incrémentale | ✅ | MVP par user story dans chaque spec |

---

## Blocages & Risques Actifs

| # | Blocage | Impact | Action requise |
|---|---|---|---|
| B1 | dbt non installé localement | 🔴 Bloque Phase 2 | `pip install dbt-postgres` |
| B2 | `manifest.json` absent | 🔴 Bloque Phases 3-4-5 | Terminer Phase 2 |
| ~~B3~~ | ~~Connexion Airflow `genbi_postgres_conn`~~ | ~~🟡~~ | ✅ Résolu |
| ~~B4~~ | ~~Modèle Ollama `qwen2.5-coder:7b` téléchargé ?~~ | ~~🟡~~ | ✅ Résolu |

---

## Références Rapides

| Document | Rôle |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Contexte projet pour Claude Code (chargé automatiquement) |
| [.specify/memory/constitution.md](.specify/memory/constitution.md) | Principes non-négociables |
| [guide_meilleures_pratiques.md](guide_meilleures_pratiques.md) | Standards techniques de chaque couche |
| [formation_claude_code.md](formation_claude_code.md) | Comment utiliser Claude Code sur ce projet |
| [formation_spec_kit.md](formation_spec_kit.md) | Méthode SDD adaptée à GenBI |
| [vision_et_objectifs.md](vision_et_objectifs.md) | Vision produit et feuille de route |
| [exploration_donnees_pharmaceutiques.md](exploration_donnees_pharmaceutiques.md) | Contexte métier pharma Dakar |
| [analyse_projet.md](analyse_projet.md) | Analyse technique complète du projet |
