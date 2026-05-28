---
name: project-genbi-context
description: Contexte complet du projet GenBI — stack, domaine, état d'avancement, décisions architecturales clés
metadata:
  type: project
---

Projet GenBI : plateforme de Business Intelligence Générative (Text-to-SQL) 100% open-source, appliquée aux officines pharmaceutiques de Dakar, Sénégal.

**Stack complète :** PostgreSQL 16 · Apache Airflow 2.8.2 · dbt-core · FastAPI · Ollama (qwen2.5-coder:7b) · React 18 + Vite · Recharts · ChromaDB · SQLGlot · LangChain · LiteLLM

**Why:** Permettre à des pharmaciens de requêter leurs données en langage naturel sans SQL, avec zéro fuite de données (LLM local).

**État (2026-05-28) :**
- Phase 1 (infra + ingestion) : terminée — DAG `ingest_pharmacy_data` opérationnel, 10 tables raw, ~4000 ventes simulées
- Phase 2 (dbt couche sémantique) : NON DÉMARRÉE — dossier `dbt_project/` vide, BLOQUE tout le reste
- Phase 3 (backend FastAPI) : squelette seulement — 2 endpoints `/` et `/api/health`
- Phase 4 (frontend React) : design system CSS prêt, page vitrine seulement
- Phase 5 (RAG ChromaDB) : future

**Décisions architecturales :**
- Ollama natif macOS (GPU Metal) — PAS dans Docker (CPU-only trop lent)
- Accès DB via `genbi_readonly` (SELECT-only) pour l'agent IA — Zero-Trust
- SQLGlot = parseur SQL, PAS un validateur de sécurité — défense principale = user read-only + parameterized queries

**How to apply:** Prioriser Phase 2 (dbt) comme prérequis bloquant avant tout développement backend ou frontend.
