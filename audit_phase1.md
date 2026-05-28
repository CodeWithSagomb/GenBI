# Audit Phase 1 — Rapport Complet
**Date** : 2026-05-28 | **Auditeur** : Claude Code

---

## Verdict Global : Phase 1 à 75% — Non Terminée

```
Infrastructure Docker     ████████████████████ 100% ✅
Sécurité PostgreSQL       ████████████████░░░░  80% ⚠️
Pipeline d'ingestion      ████░░░░░░░░░░░░░░░░  20% ❌
Backend (squelette)       ████████████████████ 100% ✅
Frontend (squelette)      ████████████████████ 100% ✅
Ollama (LLM local)        ████████████████████ 100% ✅
```

**Le problème central : le DAG `ingest_pharmacy_data` n'a jamais été déclenché.
Les tables `raw.*` n'existent pas. Il n'y a aucune donnée dans la base.**

---

## 1. Infrastructure Docker ✅ 100%

Tous les 6 services actifs sont opérationnels :

| Service | Statut | Port | Vérification |
|---|---|---|---|
| `genbi_postgres` | ✅ Up (healthy) | 5432 | `pg_isready` OK |
| `genbi_airflow_webserver` | ✅ Up (healthy) | 8080 | `/health` OK |
| `genbi_airflow_scheduler` | ✅ Up | — | Actif depuis 2h |
| `genbi_metabase` | ✅ Up | 3000 | Accessible |
| `genbi_backend` | ✅ Up | 8000 | `{"status":"healthy"}` |
| `genbi_frontend` | ✅ Up | 5173 | HTTP 200 |

**Conforme à la vision** : l'architecture multi-conteneurs est en place.
Ollama natif macOS (non-dockerisé) est accessible sur `localhost:11434` — décision architecturale correcte.

---

## 2. PostgreSQL — Sécurité ⚠️ 80%

### Ce qui fonctionne
```
✅ Base 'airflow' créée
✅ Base 'genbi' créée
✅ Schéma raw     créé dans genbi
✅ Schéma staging créé dans genbi
✅ Schéma marts   créé dans genbi
✅ User 'genbi_readonly' créé
✅ USAGE sur les 3 schémas accordé à genbi_readonly
✅ ALTER DEFAULT PRIVILEGES configuré (s'appliquera aux futures tables)
```

### Ce qui manque
```
❌ genbi_readonly n'a aucun droit SELECT sur des tables (0 rows dans role_table_grants)
   → Normal : il n'y a aucune table. Les droits s'activeront quand dbt crée les tables.
   → Risque : si dbt est exécuté par un autre user que 'postgres', ALTER DEFAULT PRIVILEGES ne s'applique pas.
   → Action requise : vérifier que dbt tourne avec l'user 'postgres' dans profiles.yml.
```

**Problème détecté :** `pg_has_role('genbi_readonly', 'pg_read_all_data', 'USAGE')` = **false**. Le rôle `pg_read_all_data` n'est pas accordé. Ce n'est pas grave si `ALTER DEFAULT PRIVILEGES` fonctionne, mais c'est une couche de sécurité manquante.

---

## 3. Pipeline d'Ingestion ❌ 20% — Bloquant

### État réel du DAG

```
DAG 'ingest_pharmacy_data'   : ✅ Chargé par le scheduler
Statut                        : ❌ PAUSED (jamais déclenché)
Connexion 'genbi_postgres_conn': ✅ Configurée via variable d'env
Historique d'exécutions       : ❌ "No data found" — zéro run

Tables raw.*                  : ❌ ZÉRO TABLE dans la base
Données                       : ❌ ZÉRO LIGNE

Ancien DAG ecommerce          : ⚠️ A tourné une fois (logs présents)
                                   mais ses données n'existent plus
                                   et le fichier DAG a été supprimé
```

### Ce que dit le DASHBOARD.md vs la réalité

| Livrable | Dashboard | Réalité |
|---|---|---|
| DAG `ingest_pharmacy_data` | ✅ | ✅ (existe) |
| 10 tables `raw.*` créées | ✅ | ❌ (0 tables) |
| ~4 000 ventes simulées | ✅ | ❌ (0 lignes) |

**Le DASHBOARD.md indique Phase 1 à 100% — c'est incorrect.**

### Pourquoi le DAG n'a pas tourné ?

1. Le DAG est **paused par défaut** (`schedule=None` + Airflow pause les nouveaux DAGs).
2. Il n'a jamais été **déclenché manuellement** depuis l'UI Airflow.
3. L'ancien DAG ecommerce a tourné une fois, puis a été supprimé avec ses données.

### Action corrective

```bash
# Option 1 : via l'UI Airflow (recommandé)
# Aller sur http://localhost:8080 → DAGs → ingest_pharmacy_data
# → Toggle ON (dépause) → Trigger DAG ▶

# Option 2 : via CLI
docker exec genbi_airflow_webserver airflow dags unpause ingest_pharmacy_data
docker exec genbi_airflow_webserver airflow dags trigger ingest_pharmacy_data
```

---

## 4. Backend FastAPI ✅ 100% (pour le squelette Phase 1)

```
✅ Tourne sur port 8000
✅ GET /          → {"status":"online","message":"..."}
✅ GET /api/health → {"status":"healthy"}
✅ CORS configuré (à restreindre en prod)
✅ Toutes les dépendances installées et importables :
   - fastapi 0.136.3
   - psycopg2-binary 2.9.12
   - sqlglot 25.34.1
   - langchain 0.2.17
   - litellm 1.86.2
   - chromadb 0.6.3
   - instructor 1.15.1
   - pydantic 2.13.4
```

**Conforme à la vision Phase 1** : le squelette est en place, les dépendances Phase 3 sont prêtes.

**Avertissements non-critiques détectés :**
- `LiteLLM botocore` warnings (module AWS non installé — normal, on n'utilise pas AWS)
- `onnxruntime cpuid_info` warning (inoffensif sur Apple Silicon)

---

## 5. Frontend React ✅ 100% (pour le squelette Phase 1)

```
✅ Tourne sur port 5173 (HTTP 200)
✅ React 18 + Vite 5
✅ Recharts + Lucide React installés
✅ Design system CSS dark mode glassmorphism
✅ Page vitrine rendue
```

---

## 6. Ollama LLM Local ✅ 100% — Bonus Phase 1

```
✅ Ollama natif macOS accessible sur localhost:11434
✅ qwen2.5-coder:7b          → TÉLÉCHARGÉ (modèle Text-to-SQL)
✅ nomic-embed-text:latest    → TÉLÉCHARGÉ (modèle embedding pour Phase 5 RAG)
```

**Excellent** : les deux modèles nécessaires pour toutes les phases sont déjà disponibles.

---

## 7. Conformité à la Vision — Analyse par Principe Constitution

| Principe | Évalué | Résultat |
|---|---|---|
| I. Souveraineté des données | Ollama local, pas d'appels externes | ✅ Respecté |
| II. Sémantique-First | dbt_project/ vide, manifest.json absent | ⏳ Phase 2 |
| III. Sécurité par architecture | genbi_readonly existe, droits schema OK | ⚠️ Tables manquantes |
| IV. Open-Source & Vendor-Agnostic | Stack 100% open-source | ✅ Respecté |
| V. Simplicité incrémentale | Squelette en place, phases séparées | ✅ Respecté |

---

## 8. Problèmes Détectés — Classés par Criticité

### 🔴 Critiques (bloquent la Phase 2)

| # | Problème | Impact | Correction |
|---|---|---|---|
| C1 | DAG `ingest_pharmacy_data` jamais déclenché | 0 données en base — Phase 2 impossible | Déclencher le DAG manuellement |
| C2 | `ingest_pharmacy_data.py` non versionné (`??` dans git) | Risque de perte du fichier | `git add airflow/dags/ingest_pharmacy_data.py && git commit` |

### 🟡 Importants (à corriger avant Phase 3)

| # | Problème | Impact | Correction |
|---|---|---|---|
| I1 | `allow_origins=["*"]` dans `main.py` | Risque CORS en production | Restreindre à `VITE_API_URL` |
| I2 | `profiles.yml` dbt absent | dbt ne peut pas se connecter | Créer `dbt_project/profiles.yml` avec user `postgres` |
| I3 | Droits SELECT `genbi_readonly` non vérifiables | Risque si dbt tourne avec un autre user | Vérifier après le premier `dbt run` |

### 🟢 Mineurs (non-bloquants)

| # | Problème | Impact | Correction |
|---|---|---|---|
| M1 | LiteLLM botocore warnings | Bruit dans les logs | Ignorer (AWS non utilisé) |
| M2 | DASHBOARD.md indique Phase 1 à 100% | Fausse représentation | Mettre à jour le dashboard |

---

## 9. Ce que la Phase 1 Apporte Réellement à la Vision

**✅ Bien construit :**
- L'architecture Docker multi-conteneurs est solide et reproductible.
- La séparation raw/staging/marts dans PostgreSQL est conforme au modèle ELT de la vision.
- L'utilisateur `genbi_readonly` respecte le principe de Zero-Trust.
- Ollama natif avec les bons modèles déjà téléchargés accélère la Phase 3.
- Le backend a toutes les dépendances pour les Phases 3, 4, 5.

**❌ Lacune principale :**
- Le pipeline d'ingestion n'a jamais tourné. La promesse "~4000 ventes simulées" n'est pas tenue.
- Sans données, la Phase 2 (dbt) ne peut pas être validée.

---

## 10. Plan de Correction — 2 actions, 10 minutes

```
Action 1 (5 min) : Déclencher le DAG
  → http://localhost:8080 → ingest_pharmacy_data → Trigger ▶
  → Vérifier : les 2 tasks passent en vert (create_pharmacy_schema + populate_pharmacy_data)

Action 2 (2 min) : Commiter le DAG
  → git add airflow/dags/ingest_pharmacy_data.py
  → git commit -m "feat: add pharmacy data ingestion DAG (10 tables, ~4000 sales)"

Vérification finale :
  → docker exec genbi_postgres psql -U postgres -d genbi \
       -c "SELECT COUNT(*) FROM raw.sales;"
  → Attendu : ~4000 lignes
```

Après ces 2 actions, Phase 1 sera réellement à 100% et la Phase 2 (dbt) pourra démarrer.
