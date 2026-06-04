# GenBI — Guide de Collaboration Claude Code

## Projet en une phrase
Plateforme de Business Intelligence Générative : les pharmaciens de Dakar interrogent leur entrepôt de données en langage naturel. LLM local (Ollama), zéro fuite de données.

## Stack & Ports
| Service | Technologie | Port |
|---|---|---|
| Base de données | PostgreSQL 16 | 5432 |
| Pipeline ETL | Apache Airflow 2.8.2 | 8080 |
| BI classique | Metabase | 3000 |
| LLM local | Ollama natif macOS | 11434 |
| API backend | FastAPI + Python 3.11 | 8000 |
| Frontend | React 18 + Vite 5 | 5173 |

## Commandes essentielles
```bash
make up          # Démarrer tous les conteneurs
make down        # Arrêter
make ps          # Vérifier l'état des conteneurs
make logs        # Logs en temps réel
make clean       # Reset complet (supprime les volumes)

# dbt (à lancer depuis dbt_project/)
dbt run          # Exécuter les transformations
dbt test         # Lancer les tests de données
dbt docs serve   # Générer la documentation
```

## Architecture des données (pipeline)
```
raw.*  →  staging.*  →  marts.*
         (dbt views)  (dbt tables)
```
- `raw` : données brutes ingérées par Airflow — NE JAMAIS modifier manuellement
- `staging` : nettoyage/renommage uniquement — matérialisé en **views**
- `marts` : tables analytiques finales — matérialisé en **tables**

## Gotchas critiques
1. **Ollama tourne nativement sur macOS** — PAS dans Docker. Le backend l'atteint via `host.docker.internal:11434`. Ne pas essayer de conteneuriser Ollama.
2. **`genbi_readonly`** (SELECT-only) pour toutes les lectures. **`genbi_write`** uniquement pour INSERT sur `raw.feedback`. Jamais `postgres` dans `core/`.
3. **RLS PostgreSQL > filtre applicatif** — l'isolation multi-pharmacie est garantie par `SET app.current_pharmacy_id` + policies RLS, pas par `WHERE pharmacy_id = ?` dans le code.
4. **SQLGlot n'est PAS un validateur de sécurité** — la vraie protection est RLS + `genbi_readonly` + sql_validator (whitelist SELECT).
5. **dbt_project/target/ est dans .gitignore** — `manifest.json` généré localement par `dbt compile`. Requis pour que le backend fonctionne.
6. **La connexion Airflow `genbi_postgres_conn` est injectée via variable d'env** dans docker-compose — déjà configurée, ne pas recréer.
7. **dbt installé localement** — dbt-postgres 1.10.0, PAS dans Docker. Lancer depuis `dbt_project/`. `dbt test` → PASS=149 WARN=0.
8. **API Keys dans `.env`** — jamais dans le code source. `core/auth.py` lit `os.environ`. 3 clés : une par pharmacie (Bourguiba / Almadies / Nation).
9. **Lifespan FastAPI** — `manifest.json` + pool DB chargés une seule fois au démarrage. Jamais dans les routes.
10. **Prompts versionnés** — `core/prompts/v1_sql_generation.txt`. Changer le comportement LLM = changer le fichier `.txt`, pas le code Python.
11. **`RETURNING` requiert SELECT** — `GRANT INSERT,SELECT ON raw.feedback TO genbi_write` (pas INSERT seul). PostgreSQL exige SELECT sur les colonnes retournées par RETURNING.
12. **Tests d'intégration dans Docker** — `docker exec genbi_backend python -m pytest tests/ -v`. Le venv local est Python 3.9 ; le container Python 3.11. Utiliser `Optional[X]` et `asyncio.wait_for` pour compatibilité 3.9.
13. **`genbi_write` créé manuellement** — `init.sql` s'exécute seulement au 1er démarrage. Si le container existe déjà, appliquer les grants via `docker exec genbi_postgres psql`.
14. **passlib 1.7.4 incompatible bcrypt 5.0.0** — `bcrypt.__about__` supprimé en v5. Utiliser `import bcrypt` directement, pas `passlib.context.CryptContext`.
15. **`get_auth_conn`** — connexion readonly SANS RLS ni `pharmacy_id`, réservée à `/auth/login`. `get_db_conn` nécessite `get_current_pharmacy` — ne pas l'utiliser avant authentification.
16. **Admin JWT → 403 pas 401** — token JWT avec `pharmacy_id: None` (rôle admin) lève `ForbiddenError` → HTTP 403. Le frontend supprime le token uniquement sur 401, garde la session sur 403.
17. **Playwright : `localhost` = IPv6** — dans le container Alpine, `localhost` résout `::1` mais Vite écoute uniquement IPv4. `playwright.config.js` utilise `http://127.0.0.1:5173`.
18. **E2E chat : injecter le token** — tests Playwright accédant au chat doivent appeler `page.addInitScript(() => localStorage.setItem('genbi_token', 'tok_e2e'))` avant `page.goto('/')`, sinon la LoginPage s'affiche.

## État d'avancement
- 🔄 Phase 6 — Qualité LLM — **en cours** — 0/22 tâches
  - T1 Benchmark : 30 questions golden + score pytest
  - T2 Seed RAG : ChromaDB pré-alimenté au démarrage
  - T3 Prompt v2 : corrections ciblées sur les échecs du benchmark
  - T4 Modèles : comparaison qwen2.5-coder:7b vs alternatives (optionnel)
  - Spec : specs/005-llm-quality/spec.md · Tasks : specs/005-llm-quality/tasks.md
- ✅ Phase 1 — Infra Docker + DAG pharmacie — validé 2026-05-28
  - 30 produits · 4 716 ventes · 11 604 lignes · 61 lots · Fév–Mai 2026 · 45M FCFA CA
- ✅ Phase 2 — dbt sémantique — validé 2026-05-29
  - 19 modèles · 149 tests PASS · manifest.json 1.0 MB · staging (views) + marts (tables)
- ✅ Phase 3 — Backend FastAPI — validé 2026-05-31 — **59/59 tests PASS**
  - 7 endpoints : `/chat` `/execute` `/query` `/interpret` `/schema` `/suggestions` `/feedback`
  - Scénario B : 1 instance · 3 pharmacies · isolation RLS (Bourguiba 1617 vs Almadies 1530 ventes)
  - genbi_readonly (lectures) + genbi_write (INSERT,SELECT raw.feedback) + RETURNING clause
  - asyncio.wait_for (compat Python 3.9 venv) · Optional[] · conftest manifest path auto-résolu
- ✅ Phase 4 — Frontend React — validé 2026-05-31 — **26/26 Vitest + 5/5 Playwright PASS**
  - ChatWindow · SQLDisplay (mode édition) · DataTable · ChartRouter (LineChart/BarChart auto)
  - Alpine ARM64 : apk add chromium (binaire Playwright glibc incompatible musl)
- ✅ Phase 5 — RAG + Feedback Loop + JWT/RBAC — validé 2026-06-03 — **114/114 backend + 44/44 Vitest + 11/11 Playwright = 169 PASS**
  - RAG few-shot : ChromaDB PersistentClient · nomic-embed-text · isolation par pharmacie · best-effort
  - Feedback loop : rating "good" → index ChromaDB · rating "bad" → ignoré · 5 tests intégration
  - JWT/RBAC : bcrypt (direct, pas passlib) · python-jose · raw.users (4 users test) · /auth/login|me|refresh
  - Frontend : LoginPage · App.jsx routing login↔chat · Bearer token · auto-logout 401 · session conservée si 403
  - Stabilisation : ForbiddenError 403 (admin) · scroll auto · badge pagination · E2E 11/11
  - core/auth.py : accepte Bearer JWT (prod) ET X-API-Key (rétrocompat tests Phase 3)

## Structure des fichiers clés
```
CLAUDE.md                               ← ce fichier
DASHBOARD.md                            ← supervision temps réel
specs/002-backend-api/spec.md           ← spécification Phase 3 (terminée)
specs/002-backend-api/tasks.md          ← 54 tâches Phase 3 (toutes ✅)
docker-compose.yml                      ← orchestration complète
data/postgres-init/init.sql             ← schémas DB + users + RLS policies
airflow/dags/ingest_pharmacy_data.py    ← pipeline d'ingestion
genbi_backend/main.py                   ← API FastAPI (lifespan + 7 routers + exception handlers)
genbi_backend/config.py                 ← configuration centralisée (BaseSettings)
genbi_backend/core/                     ← auth, database, sql_validator, dbt_parser, llm, middleware, rag, security, column_classifier
genbi_backend/api/v1/                   ← chat/, execute/, schema/, interpret/, query/, suggestions/, feedback/, auth/, admin/
genbi_backend/tests/                    ← unit/ + integration/ — 114 tests PASS
genbi_frontend/src/App.jsx              ← interface React (Phase 4-5) — routing login/chat
genbi_frontend/src/components/auth/     ← LoginPage.jsx
dbt_project/                            ← couche sémantique (Phase 2 terminée)
dbt_project/target/manifest.json        ← généré localement, requis pour le backend
```

## Conventions de code
- Python : snake_case, type hints obligatoires sur les fonctions publiques
- SQL dbt : préfixes `stg_raw__`, `fct_`, `dim_` stricts (voir guide_meilleures_pratiques.md)
- React : composants fonctionnels uniquement, hooks custom dans `src/hooks/`
- Pas de commentaires évidents — seulement les WHY non-obvieux

## Stratégie de test (par couche)
- **dbt** : tests dans les `.yml` (unique, not_null, relationships, accepted_values) — écrits avec chaque modèle
- **sql_validator.py** : TDD strict — 13 cas écrits **avant** l'implémentation
- **FastAPI** : tests unitaires (`tests/unit/`) + intégration (`tests/integration/`) via pytest + httpx
- **React** : composants avec Vitest + RTL ; flux E2E avec Playwright
- Commandes : `pytest tests/ -v` (backend) · `npm run test` (frontend) · `npm run test:e2e` (E2E)
