# Analyse Complète du Projet GenBI

### Vue d'ensemble

**GenBI** est une plateforme de **Business Intelligence Générative** 100% open-source et vendor-agnostic. L'objectif : permettre à n'importe quel utilisateur d'interroger un entrepôt de données en **langage naturel**, avec une IA locale (zéro fuite de données).

Le cas d'usage concret actuel : les **officines pharmaceutiques de Dakar, Sénégal**.

---

### Architecture Globale (Pipeline ELT)

```
Sources de données
    ↓  [Airflow - Ingestion]
PostgreSQL schema raw/
    ↓  [dbt - Transformation]
PostgreSQL schema staging/ → marts/
    ↓  [FastAPI - API REST]
LLM Ollama (qwen2.5-coder:7b) ← dbt manifest.json
    ↓  [React + Vite - Frontend]
Utilisateur Final
```

---

### `docker-compose.yml` — Infrastructure Conteneurisée

**8 services** orchestrés (dont Ollama commenté car natif macOS) :

| Service | Image | Port | Rôle |
|---|---|---|---|
| `postgres` | postgres:16-alpine | 5432 | Entrepôt de données OLAP |
| `airflow-init` | airflow:2.8.2-py3.11 | — | Init DB Airflow 1 seule fois |
| `airflow-webserver` | airflow:2.8.2-py3.11 | 8080 | UI de gestion des pipelines |
| `airflow-scheduler` | airflow:2.8.2-py3.11 | — | Exécution des DAGs |
| `metabase` | metabase/metabase:latest | 3000 | BI traditionnelle (dashboards) |
| `genbi-backend` | Build local FastAPI | 8000 | API REST + moteur IA |
| `genbi-frontend` | Build local React+Vite | 5173 | Interface utilisateur |

**Décision architecturale clé** : Ollama est exécuté **nativement sur macOS** (accélération GPU Metal) plutôt que dans Docker (CPU-only = lent). Le backend accède à Ollama via `http://host.docker.internal:11434`.

---

### `data/postgres-init/init.sql` — Sécurité Zero-Trust dès la base

Le script d'init crée :
- 2 bases : `airflow` (métadonnées Airflow) et `genbi` (données métier)
- 3 schémas dans `genbi` : `raw` → `staging` → `marts` (pipeline ELT classique)
- Un user **read-only** `genbi_readonly` : **l'IA ne peut que lire, jamais écrire/supprimer**
- Révocation des droits sur le schéma `public` par défaut

---

### `airflow/dags/ingest_pharmacy_data.py` — Pipeline d'ingestion

DAG à **déclenchement manuel** (`schedule=None`) avec 2 tâches séquentielles :

**Task 1 : `create_pharmacy_schema`** — Crée 10 tables idempotentes (`IF NOT EXISTS`) dans `raw` :

| Table | Description |
|---|---|
| `pharmacies` | 3 pharmacies de Dakar |
| `products` | 15 médicaments réels (Doliprane, Augmentin, Glucophage, Lovenox...) |
| `clients` | 100 patients sénégalais avec prénoms/noms réalistes |
| `insurers` | 5 assureurs/IPM (IPM Senelec, Sonatel, NSIA...) |
| `stocks` | 2-3 lots par produit (dont lots expirant juin 2026 pour tester les alertes) |
| `purchases` | 100 commandes auprès de 4 grossistes (UBIPHARM, LABOREX...) |
| `sales` | En-têtes de ventes (Tiers-Payant, Espèces, Wave, Orange Money) |
| `sale_details` | Lignes de ventes |
| `missed_sales` | 150 ruptures de stock enregistrées |
| `wholesaler_returns` | Retours grossistes (lots expirants) |

**Task 2 : `populate_pharmacy_data`** — Génère ~4000+ ventes sur 88 jours (1 mars → 28 mai 2026) avec une logique très réaliste :
- Patients chroniques (diabète/hypertension) qui reviennent tous les 30 jours
- Moins de ventes le dimanche
- 60% clients anonymes, 40% identifiés
- Calcul du tiers-payant (80% assureur, 20% patient)

**Note git** : `ingest_ecommerce.py` (premier DAG) a été supprimé — le projet a pivoté vers le secteur pharmaceutique.

---

### `genbi_backend/` — Cœur du Système (Phase en cours)

**Fichiers présents :**
- `main.py` : FastAPI avec seulement 2 endpoints (`/` et `/api/health`) — **le backend est un squelette**, les endpoints `/chat`, `/execute`, `/schema` de la Phase 3 ne sont pas encore implémentés
- `config.py` : Configuration Pydantic propre — LLM cible : `qwen2.5-coder:7b` via Ollama
- `requirements.txt` : Stack technique prête pour la Phase 3 :

| Dépendance | Rôle |
|---|---|
| `fastapi` + `uvicorn` | Serveur API |
| `psycopg2-binary` | Connexion PostgreSQL |
| `sqlglot` | Validation/parsing SQL (protection injection SQL) |
| `langchain` + `litellm` | Orchestration LLM |
| `instructor` | Extraction structurée JSON depuis le LLM |
| `chromadb` | Base vectorielle pour le RAG (Phase 5) |
| `pandas` | Traitement des résultats |

---

### `genbi_frontend/` — Interface Premium (Phase 4 en cours)

**Stack :** React 18 + Vite 5 + Recharts + Lucide React

**Ce qui existe :**
- `App.jsx` : Page d'accueil vitrine avec design glassmorphism dark mode
- `index.css` : Système de design premium complet (variables CSS HSL, animations pulse, effets glow)

**Ce qui manque** : L'interface de chat, les composants de visualisation, la connexion API — c'est la Phase 4.

---

### `dbt_project/` — Couche Sémantique (Phase 2 à faire)

Dossier **vide** (juste un README.txt). C'est la prochaine étape critique : sans `dbt run` et sans `manifest.json`, l'IA n'a pas de contexte sémantique pour générer du SQL correct.

---

### `exploration_donnees_pharmaceutiques.md` — Document de Conception

Document de référence business très détaillé couvrant :
- Spécificités du marché ouest-africain (FCFA, régulation des prix, Tiers-Payant, Mobile Money)
- Les 5 piliers analytiques d'une officine (Ventes, Stocks, Trésorerie, Supply Chain, Fidélisation)
- Le schéma ER complet des 10 tables

---

### État d'Avancement par Phase

| Phase | Description | Statut |
|---|---|---|
| **Phase 1** | Infrastructure Docker + Ingestion | Terminée (DAG pharmacy opérationnel) |
| **Phase 2** | dbt - Couche sémantique staging/marts | À faire (dossier vide) |
| **Phase 3** | Backend FastAPI - `/chat`, `/execute`, `/schema` | À démarrer (squelette prêt) |
| **Phase 4** | Frontend React - Interface de chat + graphiques | À démarrer (design system prêt) |
| **Phase 5** | RAG ChromaDB + feedback loop | Future |

---

### Points Techniques à Retenir

1. **Le pivot e-commerce → pharmacie** est récent (commits de ce jour). Le DAG `ingest_ecommerce.py` a été supprimé et remplacé par `ingest_pharmacy_data.py`.
2. **Le goulot d'étranglement immédiat** : la Phase 2 (dbt) bloque tout le reste — sans `manifest.json`, le backend n'a pas de métadonnées à injecter dans le prompt.
3. **La sécurité est bien pensée dès le départ** : user read-only pour l'IA, SQLGlot pour valider le SQL avant exécution.
4. **Ollama natif macOS** avec `qwen2.5-coder:7b` — bon choix pour la génération de SQL, mais il faut vérifier que le modèle est bien téléchargé (`ollama pull qwen2.5-coder:7b`).

La prochaine étape naturelle est **la Phase 2 : initialiser dbt-core, créer les modèles `staging` et `marts` pour les données pharmaceutiques, et générer le `manifest.json`**. C'est le prérequis bloquant pour tout le reste.
