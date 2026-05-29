# Feature Specification : API Backend GenBI

**Feature** : `002-backend-api`
**Créée** : 2026-05-28
**Mise à jour** : 2026-05-29
**Statut** : Draft
**Dépend de** : `001-dbt-semantic-layer` (manifest.json requis)

---

## Contexte Métier

Un pharmacien pose une question en français. Un système intelligent comprend la question, interroge les données de la pharmacie, et renvoie une réponse compréhensible avec le détail du raisonnement. Tout se passe localement — aucune donnée ne quitte le réseau.

---

## Architecture Backend

```
Requête pharmacien
      │
      ▼
POST /query          ← pipeline complet (endpoint principal frontend)
  ├── dbt_parser     ← lit manifest.json (chargé 1x au démarrage via lifespan)
  ├── llm.py         ← génère SQL (Ollama, temperature=0, timeout=30s)
  ├── sql_validator  ← refuse tout sauf SELECT
  ├── database.py    ← exécute via ThreadedConnectionPool (genbi_readonly)
  └── llm.py         ← génère insight en français (2ème appel LLM)

Endpoints modulaires (appelables indépendamment par le frontend) :
  POST /chat         ← question → SQL uniquement
  POST /execute      ← SQL → données JSON
  POST /interpret    ← données + question → insight français
  GET  /schema       ← liste des tables/colonnes du manifest
  GET  /suggestions  ← questions pré-construites pour pharmaciens
  POST /feedback     ← thumbs up/down (fondation Phase 5 RAG)
```

**Principe : thin endpoints, thick services.** Les routers gèrent HTTP. Les services gèrent la logique.

---

## User Stories & Scénarios de Test

### User Story 1 — Le pharmacien génère du SQL depuis une question (P1)

Un pharmacien tape "Quel est mon CA du mois de Mai 2026 ?" et reçoit le SQL correspondant.

**Test indépendant** : POST `/api/v1/chat` avec une question → JSON contenant `sql` et `question`.

**Scénarios d'acceptance** :
1. Question sur le CA → SQL SELECT valide ciblant `marts.fct_sales`.
2. LLM timeout (>30s) → erreur 504 avec message clair en français, pas de stack trace.
3. Question hors domaine ("mot de passe admin") → refus poli avec explication.

---

### User Story 2 — Le SQL est exécuté de façon sécurisée (P1)

Le SQL validé est exécuté via `genbi_readonly` et les résultats sont retournés en JSON structuré.

**Test indépendant** : POST `/api/v1/execute` avec SELECT valide → données JSON. POST avec DELETE → erreur 400.

**Scénarios d'acceptance** :
1. `SELECT SUM(total_amount_fcfa) FROM marts.fct_sales` → JSON `{columns, rows, row_count}`.
2. `DELETE FROM marts.fct_sales` → 400 "Opération interdite : seules les requêtes SELECT sont autorisées."
3. SQL invalide syntaxiquement → 400 avec détail du parsing.
4. Vérification : `SELECT current_user` retourne `genbi_readonly` (jamais `postgres`).

---

### User Story 3 — Le schéma est découvrable (P2)

Le frontend peut lister les tables et colonnes disponibles pour contextualiser les questions.

**Test indépendant** : GET `/api/v1/schema` → tables marts avec descriptions, schéma `raw` absent.

---

### User Story 4 — Pipeline complet en un seul appel (P1)

Le pharmacien pose une question et reçoit en une seule requête : SQL + données + insight en français.

**Test indépendant** : POST `/api/v1/query` → JSON `{sql, columns, rows, row_count, insight}`.

**Scénarios d'acceptance** :
1. "Quel est mon top 5 des produits ce mois ?" → SQL + données + insight rédigé en français professionnel.
2. Si le SQL généré est invalide → 400 avant exécution, pas d'appel LLM pour l'insight.
3. Réponse complète en moins de 30 secondes.

---

### User Story 5 — Insight en langage naturel sur des données existantes (P2)

Le frontend peut envoyer des données JSON et recevoir un résumé en français (cas : graphique déjà affiché).

**Test indépendant** : POST `/api/v1/interpret` avec `{question, results}` → champ `insight` en français.

---

### User Story 6 — Questions suggérées pour onboarding (P2)

Un pharmacien qui ne sait pas quoi demander reçoit des suggestions pertinentes.

**Test indépendant** : GET `/api/v1/suggestions` → liste de questions pré-construites non vide.

---

### User Story 7 — Feedback sur les réponses (P3)

L'utilisateur peut noter une réponse (bon/mauvais) pour alimenter la Phase 5 RAG.

**Test indépendant** : POST `/api/v1/feedback` → 201 créé, données stockées en base.

---

## Exigences Fonctionnelles

- **EF-001** : `POST /api/v1/chat` — question → SQL + question reformulée.
- **EF-002** : `POST /api/v1/execute` — SQL validé → exécution readonly → JSON `{columns, rows, row_count}`.
- **EF-003** : `GET /api/v1/schema` — tables staging+marts avec descriptions (raw exclu).
- **EF-004** : Tout SQL non-SELECT DOIT être rejeté 400 avant exécution.
- **EF-005** : Connexion DB DOIT utiliser `genbi_readonly` exclusivement (vérifiable via `SELECT current_user`).
- **EF-006** : Contexte LLM DOIT provenir exclusivement du `manifest.json` — jamais du schéma brut PostgreSQL.
- **EF-007** : Timeout LLM explicite — 30s, erreur 504 si dépassé.
- **EF-008** : `GET /api/health` — statut DB, Ollama, manifest.json (chargés via lifespan).
- **EF-009** : `POST /api/v1/query` — pipeline complet : question → SQL → données → insight français.
- **EF-010** : `POST /api/v1/interpret` — données JSON + question → insight en français (2ème appel LLM).
- **EF-011** : `GET /api/v1/suggestions` — retourne min. 5 questions pertinentes pour pharmaciens Dakar.
- **EF-012** : `POST /api/v1/feedback` — stocke `{question, sql, rating, comment}` en base (table `raw.feedback`).
- **EF-013** : `manifest.json` chargé une seule fois au démarrage via `lifespan` — jamais à chaque requête.
- **EF-014** : Pool de connexions DB initialisé au démarrage (minconn=2, maxconn=10) via `lifespan`.
- **EF-015** : Exceptions domaine (`SQLValidationError`, `LLMTimeoutError`) traduits en HTTP par handlers centralisés — jamais de HTTPException dans les services.

---

## Critères de Succès Mesurables

- **CS-001** : 80% des questions sur les ventes produisent un SQL exécutable du premier coup.
- **CS-002** : 100% des tentatives d'injection (DELETE, DROP, INSERT, UPDATE, TRUNCATE) rejetées avant exécution.
- **CS-003** : `GET /api/health` retourne "healthy" quand tous les services sont opérationnels.
- **CS-004** : Réponse `/query` complète < 30 secondes (< 15s objectif).
- **CS-005** : Zéro écriture en base via l'API — vérifiable par `SELECT current_user = genbi_readonly`.
- **CS-006** : Insight généré en français professionnel — compréhensible sans formation technique.

---

## Hypothèses

- `dbt docs generate` exécuté — `manifest.json` présent dans `dbt_project/target/`.
- Ollama natif macOS, modèle `qwen2.5-coder:7b` téléchargé, accessible via `host.docker.internal:11434`.
- Backend Docker, DB PostgreSQL sur `postgres:5432`.
- `genbi_readonly` existe avec SELECT sur staging et marts.
- psycopg2 (sync) suffit pour le MVP — le goulot est le LLM (~10s), pas la DB (~50ms).
