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
2. **L'agent IA utilise uniquement `genbi_readonly`** (SELECT-only). Toutes les connexions dans `core/` doivent utiliser cet utilisateur, jamais `postgres`.
3. **SQLGlot n'est PAS un validateur de sécurité** — la vraie protection est l'user read-only + requêtes paramétrées psycopg2.
4. **dbt_project/target/ est dans .gitignore** — le `manifest.json` est généré localement par `dbt compile`. Il faut l'avoir pour que le backend fonctionne.
5. **Le DAG Airflow utilise la connexion `genbi_postgres_conn`** — la configurer dans l'UI Airflow (Admin > Connections) avant de déclencher un DAG.

## État d'avancement
- ✅ Phase 1 — Infra Docker + DAG d'ingestion pharmacie (10 tables raw, ~4000 ventes)
- 🔄 Phase 2 — dbt (staging + marts) — **EN COURS — BLOQUANT**
- ⏳ Phase 3 — Backend FastAPI (endpoints /chat, /execute, /schema)
- ⏳ Phase 4 — Frontend React (interface chat + visualisations)
- ⏳ Phase 5 — RAG ChromaDB + feedback loop

## Structure des fichiers clés
```
CLAUDE.md                          ← ce fichier
guide_meilleures_pratiques.md      ← standards techniques du projet
exploration_donnees_pharmaceutiques.md  ← contexte métier pharma Dakar
vision_et_objectifs.md             ← feuille de route et vision produit
docker-compose.yml                 ← orchestration complète
data/postgres-init/init.sql        ← schémas DB + user read-only
airflow/dags/ingest_pharmacy_data.py    ← pipeline d'ingestion
genbi_backend/main.py              ← API FastAPI (squelette)
genbi_backend/config.py            ← configuration centralisée
genbi_frontend/src/App.jsx         ← interface React
dbt_project/                       ← couche sémantique (Phase 2)
```

## Conventions de code
- Python : snake_case, type hints obligatoires sur les fonctions publiques
- SQL dbt : préfixes `stg_raw__`, `fct_`, `dim_` stricts (voir guide_meilleures_pratiques.md)
- React : composants fonctionnels uniquement, hooks custom dans `src/hooks/`
- Pas de commentaires évidents — seulement les WHY non-obvieux
