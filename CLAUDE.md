# RuwaGenBI — Guide de Collaboration Claude Code

## Projet en une phrase
Plateforme de Business Intelligence Générative (anciennement GenBI) : les pharmaciens de Dakar interrogent leur entrepôt de données en langage naturel. LLM local (Ollama), zéro fuite de données.

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
10. **Prompts versionnés** — `core/prompts/v3_sql_generation.txt` (version active depuis session 8b+). v3 = 39 lignes, tableau de correspondances QUESTION→TABLE en tête, few-shot examples AVANT la question. v2 conservé en backup. Changer le comportement LLM = changer le fichier `.txt`, pas le code Python.
11. **`RETURNING` requiert SELECT** — `GRANT INSERT,SELECT ON raw.feedback TO genbi_write` (pas INSERT seul). PostgreSQL exige SELECT sur les colonnes retournées par RETURNING.
12. **Tests d'intégration dans Docker** — `docker exec genbi_backend python -m pytest tests/ -v`. Le venv local est Python 3.9 ; le container Python 3.11. Utiliser `Optional[X]` et `asyncio.wait_for` pour compatibilité 3.9.
13. **`genbi_write` créé manuellement** — `init.sql` s'exécute seulement au 1er démarrage. Si le container existe déjà, appliquer les grants via `docker exec genbi_postgres psql`.
14. **passlib 1.7.4 incompatible bcrypt 5.0.0** — `bcrypt.__about__` supprimé en v5. Utiliser `import bcrypt` directement, pas `passlib.context.CryptContext`.
15. **`get_auth_conn`** — connexion readonly SANS RLS ni `pharmacy_id`, réservée à `/auth/login`. `get_db_conn` nécessite `get_current_pharmacy` — ne pas l'utiliser avant authentification.
16. **Admin JWT → 403 pas 401** — token JWT avec `pharmacy_id: None` (rôle admin) lève `ForbiddenError` → HTTP 403. Le frontend supprime le token uniquement sur 401, garde la session sur 403.
17. **Playwright : `localhost` = IPv6** — dans le container Alpine, `localhost` résout `::1` mais Vite écoute uniquement IPv4. `playwright.config.js` utilise `http://127.0.0.1:5173`.
18. **E2E chat : injecter le token** — tests Playwright accédant au chat doivent appeler `page.addInitScript(() => localStorage.setItem('genbi_token', 'tok_e2e'))` avant `page.goto('/')`, sinon la LoginPage s'affiche.
19. **dim_stocks sans pharmacy_id** — `raw.stocks` n'a pas de colonne `pharmacy_id` et `dim_stocks` n'a pas de RLS. Les stocks sont un catalogue partagé dans les données de seed. Si de vraies données per-pharmacie arrivent, ajouter `pharmacy_id` à `raw.stocks` + policy RLS sur `dim_stocks`.
20. **postgres bypass RLS** — tester les requêtes de fiabilité avec `genbi_readonly`, pas `postgres`. L'utilisateur superuser ignore les RLS policies, ce qui donne des faux positifs.
21. **Dashboard thème** — `localStorage.getItem('genbi_theme')` vaut `'dark'` ou `'light'`. Appliqué via `document.documentElement.setAttribute('data-theme', theme)` dans `App.jsx`. Les variables CSS light mode sont dans `[data-theme="light"]` dans `index.css`.
22. **Hermes — modèle tool-calling** — `qwen2.5-coder:7b` génère des noms d'outils inventés (texte JSON brut) au lieu d'appeler les vrais outils. Utiliser `llama3.1:8b` dans `~/.hermes/config.yaml` — seul modèle Ollama testé qui implémente correctement le format OpenAI function-calling pour Hermes.
23. **`/api/v1/analyse` — exécution séquentielle obligatoire** — Ollama est mono-thread. `asyncio.gather` sur N sous-questions provoque des timeouts (le Nème appel dépasse 60s). Toujours exécuter les sous-questions en boucle `for/await`, jamais `asyncio.gather`.
24. **`/api/v1/analyse` — `with_insight=False` pour composé** — les sous-analyses n'ont pas d'insight individuel (économise N appels LLM, réduit la latence de moitié). L'insight n'est généré que pour les questions simples (`is_compound=False`).
25. **Mois — conversion dans `query_pipeline`** — `_humanize_months()` dans `api/v1/query/service.py` convertit les colonnes `mois`/`sale_month`/`missed_month` en noms français AVANT de retourner le résultat. S'applique à tous les endpoints qui appellent `query_pipeline` (query, analyse).
26. **ChromaDB IDs déterministes** — `core/rag.py` utilise `hashlib.sha1(question.encode()).hexdigest()[:16]` (pas `abs(hash(question))` qui change à chaque session Python). 44 exemples par pharmacie. Si des doublons réapparaissent, purger `./data/chromadb/` et redémarrer.
27. **Schéma dbt compact pour le LLM** — `core/dbt_parser._format_for_llm()` génère une ligne par table (`schema.table: col1, col2, ...`) sans descriptions (~2600 chars vs 13200 avant). Les descriptions longues dégradent la qualité SQL de qwen2.5-coder:7b. Ne pas rajouter les descriptions.
28. **`_clean_sql` défensif** — `core/llm._clean_sql()` supprime les commentaires SQL (apostrophes françaises dans `-- Note: c'est...`), extrait depuis le premier SELECT, et normalise les apostrophes dans les identifiants (`jours_jusqu'à_exp` → `jours_jusqu_à_exp`). Ne pas affaiblir ces nettoyages.
29. **q2.5-coder:7b génère des alias français avec apostrophes** — ex: `AS jours_jusqu'à_expiration`. Cause `sqlglot.errors.TokenError`. Fix dans `_clean_sql` : `re.sub(r"(\w)'(\w)", r"\1_\2", raw)`.
30. **Schema filter — `top_k=15` sur 19 tables** — `core/schema_filter.py` filtre à 80% du schéma (15/19). Descendre à 10 est trop agressif (risque d'exclure des tables nécessaires). Augmenter top_k quand schéma > 50 tables. Fallback schéma complet si Ollama/embeddings indisponibles.
31. **Insight vide si 0 lignes** — `query_pipeline` retourne `"Aucune donnée disponible pour cette période ou cette sélection."` sans appeler le LLM si `rows=[]`. Évite la réponse absurde "vous n'avez pas fourni de données".
32. **Chat multi-tour — historique limité** — `useChat.js/_buildHistory()` envoie max 3 tours (6 messages : 3 user + 3 SQL assistant). Seuls les tours avec SQL valide sont inclus. qwen2.5-coder:7b suit le contexte sur 1-2 tours fiablement, moins sur 3+.

## État d'avancement
- ✅ Session batterie 50q EN + 10 bugs insight/SQL — validé 2026-06-22 — **237/237 tests PASS**
  - Insight bilingue : `{lang_rules}` FR/EN injecté dans `build_insight_prompt()` — plus de confusion "JAMAIS mots anglais" vs `language=en`
  - Phrase complète obligatoire : règle + exemples ✓/✗ pour empêcher chiffre brut seul
  - Mois alias `month` ajouté à `_MONTH_COLS` → "octobre" pour mois 5 (mai) corrigé
  - `_clean_sql` tronque au premier `;` → texte explicatif LLM après la requête supprimé
  - Auto-détection langue question dans `useChat.js` (score lexical EN > FR → force `language=en`)
  - v3 prompt R14 : COUNT doit utiliser alias `nb_*` (jamais `total_sales` → FCFA)
  - v3 prompt : top N marge → JOIN direct `fct_purchases→dim_products` (pas `fp.sale_id`)
  - v3 prompt : "répartition ventes par type client" → `GROUP BY client_type FROM fct_sales` (pas dim_clients)
  - v3 prompt : "out of stock" → `fct_missed_sales` (jamais `quantity <= 0`)
  - v3 prompt : mapping explicite FO001 "most often" → `COUNT(*) AS nb_commandes GROUP BY wholesaler_name`
  - v1 insight : anti-bullet-list avec exemple ✓/✗ multi-éléments
  - v1 insight : "JAMAIS additionner pour obtenir un total absent des données"
- ✅ Session viz_classifier + qualité insight — validé 2026-06-22 — **237/237 tests PASS** — commit `07e5cc3`
  - `_TEMPORAL_RE` : ajout `évolue` + lookahead `par jour(?!\s+de\s+la)` → "par jour de la semaine" → bar (pas line)
  - `_RANKING_RE` : ajout mots-clés FR `le plus`, `meilleur`, `pire` → questions ranking FR → bar (pas pie)
  - `v1_insight_generation.txt` : exemples concrets ✓/✗ pour la règle anti-millions
  - 4 nouveaux tests viz_classifier (test_evolue_is_line, test_par_jour_de_la_semaine_is_bar, test_le_plus_fr_is_bar, test_meilleur_fr_is_bar)
- ✅ Roadmap Innovations — branch `feat/rag-360-coverage` — validé 2026-06-14 — **193/193 tests PASS**
  - Phase 1 `1126353` — MARS-SQL : auto-repair SQL execution-feedback loop (2 tentatives, `SQL_MAX_REPAIR_ATTEMPTS=2`)
  - Phase 2 `68b45fa` — CALM : alertes proactives LLM — 3 alertes (stock critique, lots expirants, taux service) via `/api/v1/alerts`
  - Phase 3 `c32eaee` — AP-SQL : filtrage dynamique schéma — `top_k=15`, score hybride 0.3×lexical + 0.7×cosine (nomic-embed-text)
  - Phase 4 `419bdad` — Chat multi-tour : `conversation_history` → messages LiteLLM natifs (max 3 tours / 6 messages)
  - Phase 5 ✅ — Corpus RAG synthétique : 114 exemples via claude-haiku-4-5 · 342 entrées ChromaDB (×3 pharmacies) · script : scripts/generate_rag_corpus.py
  - Gotchas : `top_k=15` fiable sur 19 tables (80% du schéma) · insight vide si `rows=[]` → message explicite sans appel LLM
  - Nouveaux fichiers : `core/schema_filter.py` · `core/prompts/v1_sql_repair.txt` · `api/v1/alerts/` (router/schemas/service)
- ✅ Phase 8b — `/api/v1/analyse` — validé 2026-06-12
  - Endpoint POST `/api/v1/analyse` : questions simples ET composées via un seul appel
  - Détection d'intention Python (regex) → 4 patterns : analyse complète · état stocks · ruptures · priorités commande
  - Questions composées → sous-questions séquentielles (Ollama mono-thread) sans insight individuel
  - Questions simples → `query_pipeline` complet avec insight
  - Frontend : `useChat.js` câblé sur `/analyse` · `ChatWindow.jsx` rendu bifurqué simple/composé
  - CSS : `.sub-analysis` + `.sub-analysis__title` pour l'affichage multi-blocs
  - Fichiers : `api/v1/analyse/__init__.py` · `schemas.py` · `service.py` · `router.py`
  - Fix mois : `_humanize_months()` dans `query_pipeline` — Février/Mars/Avril/Mai dans tableaux ET graphiques
  - Fix insight ruptures : règle "ruptures ≠ ventes" dans `v1_insight_generation.txt`
  - Fix RAG test : `range(64)` → `range(768)` dans `test_rag_flow.py` (dimension nomic-embed-text)
  - **147/147 tests PASS**
- ✅ Phase 8 — Intégration Hermes — validé 2026-06-10
  - Hermes Agent v0.16.0 dans `/Users/christsagombaye/Desktop/hermes-agent/`
  - 3 outils : `ruwagenbi_schema` · `ruwagenbi_execute` · `ruwagenbi_query` (`tools/ruwagenbi_tools.py`)
  - Toolset `ruwagenbi` déclaré dans `TOOLSETS` (toolsets.py) + dans `_HERMES_CORE_TOOLS`
  - Lancement : `cd /Users/christsagombaye/Desktop/hermes-agent && venv/bin/hermes -t ruwagenbi`
  - Modèle : `llama3.1:8b` (Ollama, 4.9 GB) — seul modèle local qui supporte le function-calling
  - Config : `~/.hermes/config.yaml` (ollama_num_ctx: 65536) · Credentials : `~/.hermes/.env`
  - **Validé** : CA total (16 364 700 FCFA ✅), lots expirants (30 ✅), RLS actif ✅
  - **Limitations connues** : Hermes = outil dev/test — llama3.1:8b instable sur analyses multi-lignes
  - **Interface principale** : frontend React (ChatWindow) via `/api/v1/analyse`
- ✅ Phase 7 — Dashboard KPIs — validé 2026-06-09 — **PR #1 ouverte (feat/dashboard-kpis → develop)**
  - 6 métriques pré-calculées via `/execute` (pas de LLM) : CA total, CA mensuel, top 5 produits, stocks sous seuil, lots expirants < 30j, ruptures
  - Bug données corrigé : `topProduits` passait par `stg_raw__sale_details` sans RLS → maintenant JOIN via `fct_sales` (RLS actif)
  - 3 corrections prompt : COUNT stocks sous seuil, COUNT ruptures, CA mensuel sans filtre temporel
  - Bug insight corrigé : LLM ne mélange plus "ruptures" dans les réponses sur péremptions
  - CSS : variables `--danger`/`--warning` dans `:root`, plus de couleurs hardcodées
  - Header sticky : `app-container` height 100vh + overflow hidden
  - Toggle jour/nuit : `data-theme` sur `<html>`, persisté en `localStorage` (`genbi_theme`)
  - Renommage : affichage **RuwaGenBI** (header, login, onglet) — dossiers techniques inchangés
  - 5 commits : `d8e1b58` → `d408580`
- ✅ Session stabilisation — validé 2026-06-09 — **34/36 tests manuels (94 %)**
  - 36 questions testées sur 8 blocs : ventes, produits, stocks, ruptures, appros, assureurs, multi-pharmacie, sécurité SQL
  - RLS vérifié : Pharma1=16 364 700 FCFA · Pharma2=16 279 550 FCFA · Pharma3=14 776 400 FCFA (valeurs distinctes ✅)
  - Correctif prompt Rule 5 : `stg_raw__sale_details` n'a pas `sale_date` — filtres temporels forcés via `fct_sales`
  - Timeouts augmentés : `LLM_SQL_TIMEOUT` 30s→60s · `LLM_INSIGHT_TIMEOUT` 20s→45s
  - Frontend validé manuellement sur les 3 comptes pharmacie
- ✅ Phase 6 — Qualité LLM — validé 2026-06-04 — **16/22 tâches (T4 optionnel)**
  - T1 Benchmark : 30 questions golden · score départ 26/30 (86 %)
  - T2 Seed RAG : ChromaDB peuplé au démarrage · fix api_base `_embed`
  - T3 Prompt v2 : 4 correctifs ciblés · **score final 30/30 (100 %)**
  - T4 Modèles : optionnel — déjà à 100 %, non nécessaire
  - Spec : specs/005-llm-quality/spec.md · Tasks : specs/005-llm-quality/tasks.md
- ✅ Phase 1 — Infra Docker + DAG pharmacie — validé 2026-05-28
  - 30 produits · 4 860 ventes · 12 207 lignes · 61 lots · Fév–Mai 2026 · ~47M FCFA CA total
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
  - Phase 6 a ajouté +8 tests → **122/122 backend PASS** (total général : 177/177)
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
genbi_backend/api/v1/                   ← chat/, execute/, schema/, interpret/, query/, analyse/, suggestions/, feedback/, auth/, admin/
genbi_backend/api/v1/analyse/           ← schemas.py · service.py (intent detection) · router.py
genbi_backend/tests/                    ← unit/ + integration/ + benchmark/ — 122 tests PASS
genbi_frontend/src/App.jsx              ← interface React — routing login/dashboard/chat + toggle thème
genbi_frontend/src/hooks/useChat.js     ← appel unique /api/v1/analyse (simple + composé)
genbi_frontend/src/hooks/useDashboard.js← 6 requêtes SQL pré-définies via /execute (Phase 7)
genbi_frontend/src/components/auth/     ← LoginPage.jsx
genbi_frontend/src/components/dashboard/← DashboardPage.jsx · KPICard.jsx · AlertTable.jsx (Phase 7)
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

## Workflow Git

### Branches
```
main      ← production stable — jamais touché directement
develop   ← intégration continue — base de tout nouveau travail
  feat/   ← nouvelles fonctionnalités
  fix/    ← corrections de bugs
  docs/   ← documentation uniquement
```

### Règle absolue
Ne JAMAIS pusher directement sur `main`. Un hook pre-push le bloque.

### Cycle de travail
```bash
# 1. Toujours partir de develop
git checkout develop && git pull origin develop

# 2. Créer une branche pour la feature
git checkout -b feat/dashboard-kpis

# 3. Travailler, commiter
git add <fichiers> && git commit -m "feat: ..."

# 4. Pousser et ouvrir une PR vers develop
git push origin feat/dashboard-kpis

# 5. Quand develop est stable → PR develop → main
```

### Convention des commits
```
feat:  nouvelle fonctionnalité
fix:   correction de bug
docs:  documentation uniquement
chore: maintenance (deps, config, refactor mineur)
test:  ajout ou modification de tests
```
