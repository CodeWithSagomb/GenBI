# GenBI — Business Intelligence Générative pour Pharmacies

> Interrogez votre entrepôt de données en **langage naturel**. LLM local, zéro fuite de données.

![Score LLM](https://img.shields.io/badge/LLM%20Benchmark-30%2F30%20(100%25)-brightgreen)
![Tests](https://img.shields.io/badge/Tests-122%20PASS-brightgreen)
![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%20%7C%20Ollama%20%7C%20PostgreSQL-blue)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Aperçu

GenBI est une plateforme de **Business Intelligence Générative** conçue pour les officines pharmaceutiques de Dakar, Sénégal. Elle permet aux pharmaciens d'interroger leur entrepôt de données en français, sans écrire une seule ligne de SQL.

```
"Quel est mon chiffre d'affaires par mois ?"
         ↓  LLM local (qwen2.5-coder:7b)
SELECT sale_month, SUM(total_amount_fcfa) FROM marts.fct_sales ...
         ↓  PostgreSQL + RLS
         ↓  Graphique automatique (LineChart / BarChart)
```

**Principe fondamental : souveraineté des données.** Tout tourne localement — le LLM, la base de données, l'API. Aucune donnée ne quitte le serveur.

---

## Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| 🗣️ **Text-to-SQL** | Question en français → SQL PostgreSQL généré par LLM |
| 📊 **Visualisation auto** | LineChart (tendances) ou BarChart (classements) détectés automatiquement |
| 🔒 **Isolation multi-pharmacie** | Row-Level Security PostgreSQL — chaque pharmacie ne voit que ses données |
| 🧠 **RAG few-shot** | ChromaDB + nomic-embed-text — exemples injectés dans le contexte du LLM |
| 🔄 **Feedback loop** | Les bonnes réponses sont réindexées dans ChromaDB pour améliorer le LLM |
| 🔐 **JWT/RBAC** | Authentification par pharmacie — token Bearer, refresh, auto-logout |
| 🏥 **LLM local** | Ollama natif — qwen2.5-coder:7b — zéro appel externe |
| 📈 **Benchmark automatique** | 30 questions golden — score 30/30 (100 %) |

---

## Stack technique

| Couche | Technologie |
|---|---|
| Base de données | PostgreSQL 16 + RLS |
| Pipeline ETL | Apache Airflow 2.8.2 |
| Couche sémantique | dbt-core 1.10.0 |
| LLM local | Ollama — qwen2.5-coder:7b + nomic-embed-text |
| RAG | ChromaDB (PersistentClient) |
| API Backend | FastAPI + Python 3.11 |
| Frontend | React 18 + Vite 5 + Recharts |
| BI classique | Metabase |
| Orchestration | Docker Compose |

---

## Architecture

```
Navigateur (React 18)
    │  questions en français
    ▼
FastAPI (port 8000)
    ├── core/llm.py          ← Prompt v2 + appel Ollama
    ├── core/rag.py          ← ChromaDB few-shot retrieval
    ├── core/sql_validator.py← Whitelist SELECT uniquement
    └── core/database.py     ← Pool readonly + RLS setter
    │  SELECT + SET app.current_pharmacy_id
    ▼
PostgreSQL 16
    ├── raw.*       ← données brutes (Airflow)
    ├── staging.*   ← nettoyage dbt (views)
    └── marts.*     ← tables analytiques dbt
```

**Modèle de sécurité :**
- `genbi_readonly` — SELECT uniquement sur `staging.*` et `marts.*`
- `genbi_write` — INSERT + SELECT sur `raw.feedback` uniquement
- RLS PostgreSQL sur `fct_sales` — isolation automatique par `pharmacy_id`

---

## Démarrage rapide

### Prérequis

- Docker Desktop
- [Ollama](https://ollama.ai) installé nativement (macOS / Linux)
- dbt-postgres 1.10.0 (`pip install dbt-postgres==1.10.0`)

### Installation

```bash
# 1. Cloner le repo
git clone https://github.com/CodeWithSagomb/GenBI.git
cd GenBI

# 2. Télécharger les modèles Ollama
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text

# 3. Démarrer tous les services
make up

# 4. Générer le manifest dbt (requis au démarrage du backend)
cd dbt_project && dbt run && dbt compile && cd ..

# 5. Ouvrir l'interface
open http://localhost:5173
```

### Comptes de démo

| Pharmacie | Email | Mot de passe |
|---|---|---|
| Bourguiba | bourguiba@pharma.sn | test123 |
| Almadies | almadies@pharma.sn | test123 |
| Nation | nation@pharma.sn | test123 |

---

## Données de démonstration

Les données sont générées automatiquement par Airflow pour 3 pharmacies fictives (Dakar, Sénégal) :

| Métrique | Valeur |
|---|---|
| Période | Février – Mai 2026 |
| Produits | 30 (16 classes thérapeutiques) |
| Ventes (Bourguiba) | 1 617 transactions |
| CA total 2026 | 15 074 800 FCFA |
| Ruptures de stock | 64 événements |
| Clients distincts | 100 |

---

## Exemples de questions

```
Quel est le CA total de ma pharmacie en 2026 ?
  → 15 074 800 FCFA

Quels sont mes 5 produits les plus vendus en quantité ?
  → BarChart automatique

Quel est mon chiffre d'affaires par mois ?
  → LineChart — Fév / Mars / Avril / Mai 2026

Quels produits sont en rupture de stock ?
  → Liste de 26 médicaments

Quel est le CA total des médicaments hors parapharmacie ?
  → 11 318 600 FCFA

Quels sont les médicaments antipaludéens que nous vendons ?
  → Tableau — 2 médicaments
```

---

## Tests

```bash
# Backend (dans le container)
docker exec genbi_backend python -m pytest tests/ -v
# → 122/122 PASS

# Frontend
cd genbi_frontend && npm run test
# → 44/44 Vitest PASS

# E2E Playwright
cd genbi_frontend && npm run test:e2e
# → 11/11 PASS

# Benchmark LLM (30 questions golden)
docker exec genbi_backend python3 -m tests.benchmark.run_benchmark
# → 30/30 (100 %)
```

---

## État d'avancement

| Phase | Description | Statut |
|---|---|---|
| Phase 1 | Infrastructure Docker + Ingestion Airflow | ✅ |
| Phase 2 | Couche sémantique dbt (19 modèles) | ✅ |
| Phase 3 | API Backend FastAPI (9 endpoints) | ✅ |
| Phase 4 | Interface de Chat React | ✅ |
| Phase 5 | RAG + Feedback Loop + JWT/RBAC | ✅ |
| Phase 6 | Qualité LLM — Benchmark + Prompt v2 | ✅ **30/30** |

---

## Structure du projet

```
GenBI/
├── airflow/dags/          ← Pipeline d'ingestion Airflow
├── data/postgres-init/    ← Schémas DB + utilisateurs + RLS
├── dbt_project/           ← Couche sémantique (19 modèles)
├── genbi_backend/
│   ├── api/v1/            ← 9 routers FastAPI
│   ├── core/              ← llm, rag, sql_validator, auth, database
│   ├── tests/             ← 122 tests (unit + integration + benchmark)
│   └── core/prompts/      ← Prompts versionnés (v1, v2)
├── genbi_frontend/
│   ├── src/components/    ← ChatWindow, DataTable, ChartRouter, LoginPage
│   └── tests/             ← Vitest + Playwright E2E
├── specs/                 ← Spécifications par phase
├── CLAUDE.md              ← Guide de collaboration IA
└── DASHBOARD.md           ← Tableau de bord de supervision
```

---

## Principes de conception

1. **Souveraineté des données** — LLM local uniquement, 0 appel externe
2. **Sémantique-First** — `manifest.json` dbt comme seule source de vérité du schéma
3. **Sécurité Zero-Trust** — `genbi_readonly` SELECT-only + RLS PostgreSQL + whitelist SQL
4. **Open-Source & Vendor-Agnostic** — Ollama, ChromaDB, dbt, FastAPI, React
5. **Simplicité incrémentale** — MVP par phase, spec avant code

---

## Licence

MIT — voir [LICENSE](LICENSE)

---

*Développé dans le cadre d'un projet de recherche appliquée sur l'IA générative pour le secteur pharmaceutique en Afrique de l'Ouest.*
