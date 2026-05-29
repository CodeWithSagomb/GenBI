# Feature Specification : API Backend GenBI

**Feature** : `002-backend-api`
**Créée** : 2026-05-28
**Mise à jour** : 2026-05-29
**Statut** : Draft
**Dépend de** : `001-dbt-semantic-layer` (manifest.json requis)

---

## Contexte Métier

Un pharmacien pose une question en français. Un système intelligent comprend la question, interroge les données de **sa** pharmacie uniquement, et renvoie une réponse compréhensible avec le SQL généré. Tout se passe localement — aucune donnée ne quitte le réseau.

**Déploiement Scénario B** : une seule instance FastAPI sert les 3 pharmacies de Dakar. Chaque pharmacie est identifiée par une API Key. Un pharmacien de Bourguiba ne peut jamais accéder aux données des Almadies — isolation garantie au niveau base de données (PostgreSQL Row Level Security).

---

## Architecture Backend

```
Requête pharmacien (header X-API-Key: pk_bourguiba_xxx)
      │
      ▼
Middleware (request_id + logging JSON + rate limiting 10req/min/clé)
      │
      ▼
Auth (API Key → pharmacy_id=1) ← Depends(get_current_pharmacy)
      │
      ▼
RLS PostgreSQL (SET app.current_pharmacy_id = 1)
      │                              ← isolation garantie au niveau DB
      ▼
POST /query          ← endpoint principal frontend
  ├── dbt_parser     ← manifest.json (chargé 1x via lifespan)
  ├── llm.py         ← génère SQL (temperature=0, timeout=30s)
  ├── sql_validator  ← refuse tout sauf SELECT
  ├── database.py    ← ThreadedConnectionPool (genbi_readonly)
  └── llm.py         ← génère insight en français (temperature=0.3)

Endpoints modulaires :
  POST /chat         ← question → SQL
  POST /execute      ← SQL → données JSON (paginées)
  POST /interpret    ← données + question → insight français
  GET  /schema       ← tables/colonnes du manifest
  GET  /suggestions  ← questions pré-construites pour pharmaciens
  POST /feedback     ← thumbs up/down (genbi_write → raw.feedback)
```

**Principes d'architecture :**
- **Thin endpoints, thick services** — les routers gèrent HTTP, les services gèrent la logique
- **Domain exceptions** — services lèvent des exceptions domaine, jamais HTTPException
- **Lifespan** — manifest + pool DB initialisés une seule fois au démarrage
- **RLS > filtre applicatif** — l'isolation des données est garantie par PostgreSQL, pas par le code

---

## User Stories & Scénarios de Test

### User Story 1 — Le pharmacien génère du SQL depuis une question (P1)

Un pharmacien de Bourguiba tape "Quel est mon CA de Mai 2026 ?" et reçoit le SQL correspondant, filtré sur sa pharmacie.

**Test indépendant** : POST `/api/v1/chat` avec `X-API-Key: pk_bourguiba` → JSON contenant `sql` et `question`.

**Scénarios d'acceptance** :
1. Question sur le CA → SQL SELECT valide ciblant `marts.fct_sales`.
2. LLM timeout (>30s) → erreur 504 avec message en français, pas de stack trace.
3. Question hors domaine → refus poli avec explication de ce que l'API peut faire.

---

### User Story 2 — Le SQL est exécuté de façon sécurisée (P1)

Le SQL validé est exécuté via `genbi_readonly` avec RLS actif. Les résultats sont paginés.

**Test indépendant** : POST `/api/v1/execute` avec SELECT → données JSON. POST avec DELETE → 400.

**Scénarios d'acceptance** :
1. `SELECT SUM(total_amount_fcfa) FROM marts.fct_sales` → JSON `{columns, rows, row_count, page, limit}`.
2. `DELETE FROM marts.fct_sales` → 400 "Opération interdite : seules les requêtes SELECT sont autorisées."
3. SQL invalide → 400 avec détail du parsing.
4. `SELECT current_user` retourne `genbi_readonly` — jamais `postgres`.
5. Requête sans `X-API-Key` → 401 Unauthorized.

---

### User Story 3 — Le schéma est découvrable (P2)

Le frontend liste les tables et colonnes disponibles pour contextualiser les questions.

**Test indépendant** : GET `/api/v1/schema` → tables marts avec descriptions, schéma `raw` absent.

---

### User Story 4 — Pipeline complet en un seul appel (P1)

Question → SQL → données → insight en français, dans une seule requête.

**Test indépendant** : POST `/api/v1/query` → JSON `{sql, columns, rows, row_count, insight}`.

**Scénarios d'acceptance** :
1. "Top 5 produits ce mois ?" → SQL + données + insight rédigé en français professionnel.
2. SQL invalide généré → 400 avant exécution, insight non généré.
3. Réponse complète < 30 secondes.

---

### User Story 5 — Insight en langage naturel (P2)

Le frontend envoie des données déjà affichées et reçoit un résumé en français.

**Test indépendant** : POST `/api/v1/interpret` avec `{question, results}` → `{insight}` en français.

---

### User Story 6 — Questions suggérées (P2)

Un pharmacien qui ne sait pas quoi demander reçoit des suggestions contextuelles.

**Test indépendant** : GET `/api/v1/suggestions` → liste ≥ 5 questions pertinentes pharmacie Dakar.

---

### User Story 7 — Feedback sur les réponses (P3)

L'utilisateur note une réponse (bon/mauvais) pour alimenter la Phase 5 RAG.

**Test indépendant** : POST `/api/v1/feedback` → 201. Données stockées dans `raw.feedback`.

---

### User Story 8 — Isolation multi-pharmacie garantie (P1)

Un pharmacien de Bourguiba ne peut jamais voir les données des Almadies, même avec un SQL crafté manuellement.

**Test indépendant** : avec `X-API-Key: pk_bourguiba`, un `SELECT * FROM marts.fct_sales` ne retourne que les ventes `pharmacy_id = 1` — la RLS filtre automatiquement.

**Scénarios d'acceptance** :
1. Clé Bourguiba + `SELECT * FROM marts.fct_sales` → uniquement les lignes `pharmacy_id = 1`.
2. Clé Almadies + même requête → uniquement les lignes `pharmacy_id = 2`.
3. Clé inconnue → 401 immédiat, avant toute exécution.

---

## Exigences Fonctionnelles

### Endpoints
- **EF-001** : `POST /api/v1/chat` — question → `{sql, question}`.
- **EF-002** : `POST /api/v1/execute` — SQL validé → `{columns, rows, row_count, page, limit}`. Pagination : `limit` max 500, défaut 100.
- **EF-003** : `GET /api/v1/schema` — tables staging+marts avec descriptions (raw exclu).
- **EF-004** : `POST /api/v1/query` — pipeline complet → `{sql, columns, rows, row_count, insight}`.
- **EF-005** : `POST /api/v1/interpret` — `{question, results}` → `{insight}`.
- **EF-006** : `GET /api/v1/suggestions` — ≥ 5 questions pré-construites.
- **EF-007** : `POST /api/v1/feedback` — stocke dans `raw.feedback` via `genbi_write`.
- **EF-008** : `GET /api/health` — statut `{db, ollama, manifest, manifest_models}`.

### Sécurité
- **EF-009** : Tout SQL non-SELECT → rejeté 400 avant exécution.
- **EF-010** : Connexion DB → `genbi_readonly` exclusivement (sauf feedback → `genbi_write`).
- **EF-011** : PostgreSQL Row Level Security sur `marts.*` et `staging.*` — isolation garantie au niveau DB, pas applicatif.
- **EF-012** : Authentification via header `X-API-Key` — 401 si absente ou invalide.
- **EF-013** : Rate limiting — 10 requêtes/minute/clé (en mémoire, pas de Redis pour MVP).
- **EF-014** : CORS — origine autorisée : `http://localhost:5173` uniquement.

### Maintenabilité
- **EF-015** : Contexte LLM → exclusivement `manifest.json` — jamais le schéma brut PostgreSQL.
- **EF-016** : Timeout LLM → 30s, erreur 504 si dépassé.
- **EF-017** : `manifest.json` + pool DB chargés via `lifespan` — jamais à chaque requête.
- **EF-018** : Logging structuré JSON — chaque log inclut `request_id`, `pharmacy_id`, `duration_ms`.
- **EF-019** : `request_id` (UUID) généré par middleware — présent dans chaque réponse HTTP (`X-Request-ID`).
- **EF-020** : Domain exceptions (`SQLValidationError`, `LLMTimeoutError`, etc.) traduits en HTTP par handlers centralisés dans `main.py` — jamais de `HTTPException` dans les services.
- **EF-021** : Prompts versionnés dans `core/prompts/` — changer un prompt = changer un fichier `.txt`, pas du code Python.
- **EF-022** : `temperature=0.0` obligatoire pour génération SQL. `temperature=0.3` pour insight.

---

## Critères de Succès Mesurables

- **CS-001** : 80% des questions sur les ventes produisent un SQL exécutable du premier coup.
- **CS-002** : 100% des tentatives d'injection (DELETE, DROP, INSERT, UPDATE, TRUNCATE) rejetées avant exécution.
- **CS-003** : `GET /api/health` retourne "healthy" quand tous les services sont opérationnels.
- **CS-004** : Réponse `/query` complète < 30 secondes (< 15s objectif).
- **CS-005** : `SELECT current_user` retourne `genbi_readonly` — zéro écriture via l'API (sauf feedback).
- **CS-006** : Insight généré en français professionnel, compréhensible sans formation technique.
- **CS-007** : Isolation RLS vérifiable — clé Bourguiba ne retourne jamais de données `pharmacy_id != 1`.

---

## Hypothèses

- `manifest.json` présent dans `dbt_project/target/` (Phase 2 terminée).
- Ollama natif macOS, `qwen2.5-coder:7b` téléchargé, accessible via `host.docker.internal:11434`.
- Backend Docker, PostgreSQL sur `postgres:5432`.
- `genbi_readonly` : SELECT sur staging et marts.
- `genbi_write` : INSERT uniquement sur `raw.feedback` (à créer en Phase 3).
- RLS PostgreSQL activé sur `marts.*` via policy `current_setting('app.current_pharmacy_id')`.
- psycopg2 sync suffit pour MVP — goulot = LLM (~10s), pas DB (~50ms).
