# RuwaGenBI — Roadmap Innovations Ingénierie

> Document de supervision — basé sur la recherche académique 2024-2025
> (MARS-SQL, Track-SQL, CALM, AP-SQL, SIGMOD 2025)
> Dernière mise à jour : 2026-06-14

---

## Diagnostic — État actuel du pipeline

```
question → RAG ChromaDB (top-3) → prompt v3 (34 domaines, 2914 chars)
         → qwen2.5-coder:7b → _clean_sql() → execute PostgreSQL
         → generate_insight() → réponse JSON
```

### Lacunes critiques confirmées

| # | Problème | Localisation | Impact |
|---|---|---|---|
| L1 | Pas de retry SQL | `query/service.py` — lève `DatabaseError` immédiatement | ~20% questions échouent inutilement |
| L2 | Chat stateless | `useChat.js` ne transmet rien à l'API | "Et leur marge ?" incompréhensible |
| L3 | Alertes sans narration LLM | `useDashboard.js` — SQL brut | Dashboard peu actionnable |
| L4 | Corpus RAG = 52 exemples manuels | `golden_questions.py` statique | Mauvaise généralisation sur nouveaux domaines |
| L5 | Schéma toujours complet dans le prompt | `dbt_parser.py` — 2914 chars croissant | Contexte saturé à long terme |

---

## Plan d'implémentation — 5 Phases

---

### Phase 1 — Auto-repair SQL
**Inspiration : MARS-SQL (ICLR 2025) — execution-feedback loop**
**Complexité : S | Estimé : 2-3h | Risque : Faible | Statut : [ ] À faire**

#### Principe
Quand PostgreSQL retourne une erreur, renvoyer `(erreur + SQL raté + question)` au LLM
avec un prompt `FIX_SQL`. 60-70% des erreurs syntaxiques se corrigent en un seul retry.

#### Fichiers à modifier

| Fichier | Action |
|---|---|
| `genbi_backend/core/prompts/v1_sql_repair.txt` | Créer — prompt repair avec `{schema}`, `{question}`, `{failed_sql}`, `{error_message}` |
| `genbi_backend/core/llm.py` | Ajouter `repair_sql(schema, question, failed_sql, error_message)` |
| `genbi_backend/api/v1/query/service.py` | Boucle 2 tentatives max sur `psycopg2.Error` |
| `genbi_backend/config.py` | Ajouter `SQL_MAX_REPAIR_ATTEMPTS: int = 2` et `SQL_REPAIR_TIMEOUT: int = 30` |

#### Structure du prompt repair
```
Tu es expert SQL PostgreSQL.
Le SQL suivant a échoué. Corrige-le.
Génère UNIQUEMENT le SELECT SQL corrigé — sans point-virgule.

<schema_dbt>{schema}</schema_dbt>
<question>{question}</question>
<failed_sql>{failed_sql}</failed_sql>
<error>{error_message}</error>
```

#### Logique de retry dans service.py
```
tentative 0 : SQL généré normalement
  → psycopg2.Error → repair_sql() → tentative 1
    → psycopg2.Error → repair_sql() → tentative 2
      → psycopg2.Error → DatabaseError levée (comportement actuel)
```

#### Cas limites
- `LLMTimeoutError` pendant repair → ne pas catcher, laisser propager
- SQL repair génère DELETE/UPDATE → bloqué par `validate_sql()` avant exécution
- `SQLValidationError` sur le SQL réparé → continuer au retry suivant

#### Tests
- `test_repair_prompt_contient_failed_sql_et_error()` dans `test_llm_prompt_builder.py`
- `test_query_repare_sql_invalide()` dans `test_query_endpoint.py`
  (mock `generate_sql` retourne SQL cassé au 1er appel, SQL valide au 2ème)

---

### Phase 2 — Alertes proactives
**Inspiration : CALM (arxiv 2508.21273) + AAD-LLM (arxiv 2411.00914)**
**Complexité : S | Estimé : 3-4h | Risque : Faible | Indépendant | Statut : [ ] À faire**

#### Principe
Endpoint GET `/api/v1/alerts` qui tourne 3 requêtes SQL prédéfinies au chargement
du dashboard et retourne des alertes en langage naturel via `generate_insight()`.

#### Fichiers à créer/modifier

| Fichier | Action |
|---|---|
| `genbi_backend/api/v1/alerts/__init__.py` | Créer |
| `genbi_backend/api/v1/alerts/schemas.py` | `Alert`, `AlertsResponse` |
| `genbi_backend/api/v1/alerts/service.py` | `_ALERT_QUERIES` + `generate_alerts()` |
| `genbi_backend/api/v1/alerts/router.py` | `GET /api/v1/alerts` |
| `genbi_backend/main.py` | Enregistrer `alerts_router` |
| `genbi_frontend/src/services/api.js` | Ajouter `getAlerts()` |
| `genbi_frontend/src/hooks/useAlerts.js` | Créer — pattern identique à `useDashboard.js` |
| `genbi_frontend/src/components/dashboard/DashboardPage.jsx` | Section "Alertes intelligentes" |

#### 3 alertes prédéfinies

```python
_ALERT_QUERIES = [
    {
        "id": "stock_critique",
        "severity": "danger",
        "title": "Stocks sous seuil de sécurité",
        "sql": """SELECT commercial_name AS produit,
                         quantity_in_stock AS stock_actuel,
                         safety_stock_threshold AS seuil
                  FROM marts.dim_stocks
                  WHERE is_below_safety_threshold = TRUE
                  ORDER BY quantity_in_stock ASC""",
    },
    {
        "id": "lots_expirants",
        "severity": "warning",
        "title": "Lots expirant dans 30 jours",
        "sql": """SELECT commercial_name AS produit,
                         batch_number AS lot,
                         expiration_date AS expiration,
                         days_until_expiry AS jours_restants
                  FROM marts.dim_stocks
                  WHERE days_until_expiry >= 0 AND days_until_expiry <= 30
                  ORDER BY days_until_expiry ASC""",
    },
    {
        "id": "taux_service",
        "severity": "info",
        "title": "Taux de service fournisseurs",
        "sql": """SELECT wholesaler_name AS fournisseur,
                         ROUND(100.0 * SUM(quantity_received)
                               / NULLIF(SUM(quantity_ordered), 0), 1) AS taux_service_pct
                  FROM marts.fct_purchases
                  GROUP BY wholesaler_name
                  ORDER BY taux_service_pct ASC""",
    },
]
```

#### Règle de performance
Appeler `generate_insight()` **uniquement si** `row_count > 0` — éviter les appels
Ollama inutiles si la pharmacie n'a pas d'alertes actives.

#### Cas limites
- RLS actif : `get_db_conn` isole automatiquement par pharmacie
- `dim_stocks` sans pharmacy_id : partagé entre pharmacies par design (documenté)
- Tous résultats vides → `alerts: []` sans appel LLM

#### Tests
- `test_alerts_retourne_200()`, `test_alerts_sans_auth_401()`, `test_alerts_structure_response()`
- `test_alerts_rls_isolation()` : Bourguiba vs Almadies → rows différents

---

### Phase 3 — Schema filtering dynamique
**Inspiration : AP-SQL (arxiv 2506.03598) + Bidirectional Schema Linking (arxiv 2510.14296)**
**Complexité : M | Estimé : 4-6h | Risque : Moyen | Prérequis pour Phase 4 | Statut : [ ] À faire**

#### Principe
Avant `build_sql_prompt()`, filtrer le schéma aux 10-15 tables/colonnes les plus
pertinentes via matching lexical + cosine similarity nomic-embed-text.
Réutilise `_embed()` de `rag.py` — pas de nouvelle dépendance.

#### Fichiers à créer/modifier

| Fichier | Action |
|---|---|
| `genbi_backend/core/schema_filter.py` | Créer — `parse_schema_to_table_records()`, `filter_schema_for_question()` |
| `genbi_backend/main.py` | Précalculer `app.state.schema_embeddings` au démarrage |
| `genbi_backend/api/v1/query/service.py` | Appliquer filtre avant `generate_sql()` |
| `genbi_backend/api/v1/query/router.py` | Passer `schema_embeddings` depuis `app.state` |
| `genbi_backend/api/v1/analyse/service.py` | Même modification |

#### Stratégie hybride dans schema_filter.py
```python
def filter_schema_for_question(schema_text, question, top_k=15, embed_fn=None):
    # 1. Matching lexical exact (gratuit) — priorité max
    # 2. Cosine similarity sur embeddings nomic-embed-text
    # 3. Tables core toujours incluses :
    #    marts.fct_sales, marts.dim_products, staging.stg_raw__sale_details
    # 4. Fallback schéma complet si embed_fn=None ou exception
```

#### Tables core — toujours incluses dans le top-k
- `marts.fct_sales`
- `marts.dim_products`
- `staging.stg_raw__sale_details`

#### Cas limites
- Ollama indisponible au démarrage → `schema_embeddings = None` → fallback schéma complet
- Question cross-domaine → whitelist tables core garantit la couverture minimale
- `reload_manifest()` admin → recomputer les embeddings dans le même handler
- ROI limité aujourd'hui (19 modèles) — ROI fort à >50 modèles

#### Tests
- `test_filter_retourne_tables_pertinentes()` : "CA total" → `marts.fct_sales` présent
- `test_filter_fallback_si_embed_indisponible()` : mock `_embed` lève exception → schéma complet retourné
- `test_tables_core_toujours_presentes()` : n'importe quelle question → 3 tables core présentes

---

### Phase 4 — Chat multi-tour / mémoire conversationnelle
**Inspiration : Track-SQL (NAACL 2025, arxiv 2603.05996) + SQLong (arxiv 2502.16747)**
**Complexité : M | Estimé : 5-7h | Risque : Moyen | Dépend de Phase 3 | Statut : [ ] À faire**

#### Principe
Fenêtre glissante de 3 tours `{question, sql, summary}` envoyée par le frontend.
Injectée dans un nouveau prompt v4 via `{conversation_history}`.
Permet : "Et leur marge ?" après "Quels sont mes top 5 produits ?"

#### Fichiers à modifier

| Fichier | Action |
|---|---|
| `genbi_frontend/src/hooks/useChat.js` | Construire et envoyer `conversation_history` (3 derniers tours) |
| `genbi_frontend/src/services/api.js` | `analyse(question, conversation_history=[])` |
| `genbi_backend/api/v1/analyse/schemas.py` | Ajouter `ConversationTurn` + champ `conversation_history` dans `AnalyseRequest` |
| `genbi_backend/core/llm.py` | `build_sql_prompt(conversation_history=None)` + `generate_sql(conversation_history=None)` |
| `genbi_backend/core/prompts/v4_sql_generation.txt` | Créer depuis v3 + placeholder `{conversation_history}` |
| `genbi_backend/config.py` | `SQL_PROMPT_VERSION = "v4_sql_generation"` |
| `genbi_backend/api/v1/analyse/service.py` | Propager `conversation_history` jusqu'à `query_pipeline()` |

#### Sérialisation dans useChat.js
```javascript
const history = messages
  .filter(m => m.role === 'ai' && !m.error && m.sub_analyses?.length)
  .slice(-3)  // 3 tours max pour rester dans 8K tokens
  .map(m => ({
    question: m.question,
    sql: m.sub_analyses[0]?.sql ?? '',
    summary: (m.sub_analyses[0]?.insight ?? '').slice(0, 150),
  }))
```

#### Bloc injecté dans le prompt
```xml
<conversation_history>
Tour 1:
  Question: quels sont mes top 5 produits ?
  SQL: SELECT pd.commercial_name, SUM(...) FROM ...
  Résultat: Doliprane 1er avec 2.1M FCFA
Tour 2:
  ...
</conversation_history>
```

#### Rétrocompatibilité
`conversation_history=[]` → `{conversation_history}` = `""` → prompt identique à v3.
Endpoint `/query` (direct SQL) non modifié.

#### Contrainte tokens
Schema filtré (Phase 3) ~1500 chars + 3 tours × ~250 chars = ~2250 chars.
Total prompt ~4000 chars. Safe dans 8K tokens de qwen2.5-coder:7b.

#### Tests
- `test_conversation_history_injecte_bloc_xml()` dans `test_llm_prompt_builder.py`
- `test_prompt_sans_history_identique_a_avant()` — non-régression
- `test_analyse_avec_history_passe_en_parametre()` — pas d'erreur 422

---

### Phase 5 — Corpus RAG synthétique
**Inspiration : SIGMOD 2025 Data+AI (LLM4Data, Tsinghua)**
**Complexité : M | Estimé : 4-6h | Script one-shot | Statut : [ ] À faire**

#### Principe
Script Python qui appelle claude-haiku-4-5 une seule fois pour générer ~200 paires
(question, SQL) par domaine métier sur le schéma dbt. Enrichit ChromaDB en permanence
sans travail manuel.

#### Fichiers à créer/modifier

| Fichier | Action |
|---|---|
| `genbi_backend/scripts/generate_rag_corpus.py` | Créer — script CLI standalone |
| `genbi_backend/scripts/synthetic_questions.py` | Généré par le script — même format que `golden_questions.py` |
| `genbi_backend/config.py` | Ajouter `ANTHROPIC_API_KEY: str = ""` |
| `genbi_backend/requirements.txt` | Ajouter `anthropic>=0.25.0,<1.0.0` |
| `genbi_backend/main.py` | Merger `golden_questions + synthetic_questions` au seed RAG |

#### Domaines couverts (14)
`ca_simple`, `produits`, `clients`, `ruptures`, `stocks`, `achats`, `assureurs`,
`marge`, `retours`, `temporel`, `tva`, `fidelite`, `panier`, `generiques`

#### Prompt envoyé à Claude Haiku
```
Tu es expert SQL PostgreSQL pour pharmacies en Afrique de l'Ouest.
Génère exactement {n} paires (question français, SQL PostgreSQL) pour le domaine "{domain}".

Schéma : {schema}

Règles : SELECT uniquement · préfixe schéma obligatoire · pas de WHERE pharmacy_id (RLS actif)
Varier les formulations : synonymes, niveaux de détail différents.

Questions existantes à éviter : {existing_questions}

Format JSON strict : [{"question": "...", "sql": "..."}, ...]
```

#### Pipeline de validation
```
Haiku génère → validate_sql() sqlglot → tables existent dans schéma → insert ChromaDB
                        ↓ invalide
                   loguer + ignorer (~20-30% attendu)
```

#### Cas limites
- Rate limiting Anthropic → `time.sleep(0.5)` entre domaines
- Doublons → `hashlib.sha1` déterministe = upsert idempotent dans ChromaDB
- Script one-shot — ne pas exécuter au démarrage du backend

#### Tests
- Mode `--dry-run` : 2 paires par domaine, JSON valide, SQL valide
- `test_rag_seed_merge_golden_synthetic()` dans `test_rag_seed.py`

---

## Séquencement et dépendances

```
Semaine 1   Phase 1 — Auto-repair SQL ─────────────────────────────────────┐
                                                                            │
Semaine 2   Phase 2 — Alertes proactives ──────────────────────────────────┤ parallèle
            Phase 3 — Schema filtering ─────────────────────────────┐      │
                                                                     │      │
Semaine 3   ──────────────────────────── Phase 4 — Multi-tour ◄──────┘      │
                                                                            │
Semaine 4   ──────────────────────────────────────── Phase 5 — RAG corpus ◄─┘
```

---

## Tableau de synthèse

| Phase | Innovation | Complexité | Temps | Risque | Dépend de |
|---|---|---|---|---|---|
| 1 | Auto-repair SQL | S | 2-3h | Faible | — |
| 2 | Alertes proactives | S | 3-4h | Faible | — |
| 3 | Schema filtering | M | 4-6h | Moyen | — |
| 4 | Chat multi-tour | M | 5-7h | Moyen | Phase 3 |
| 5 | Corpus RAG synthétique | M | 4-6h | Moyen | Phase 1 stable |

**Total estimé : 3-4 semaines**

---

## Suivi d'avancement

| Phase | Statut | Date début | Date fin | Notes |
|---|---|---|---|---|
| Phase 1 — Auto-repair SQL | ⬜ À faire | | | |
| Phase 2 — Alertes proactives | ⬜ À faire | | | |
| Phase 3 — Schema filtering | ⬜ À faire | | | |
| Phase 4 — Chat multi-tour | ⬜ À faire | | | |
| Phase 5 — Corpus RAG | ⬜ À faire | | | |

---

## Sources de recherche

| Technique | Papier | Lien |
|---|---|---|
| Auto-repair (execution-feedback) | MARS-SQL, ICLR 2025 | arxiv.org/abs/2511.01008 |
| Multi-tour | Track-SQL, NAACL 2025 | arxiv.org/abs/2603.05996 |
| Multi-tour contexte étendu | SQLong, 2025 | arxiv.org/abs/2502.16747 |
| Alertes anomalies | CALM, 2025 | arxiv.org/abs/2508.21273 |
| Alertes zero-shot | AAD-LLM, 2024 | arxiv.org/abs/2411.00914 |
| Schema filtering | AP-SQL, EITCE 2025 | arxiv.org/abs/2506.03598 |
| Schema linking bidirectionnel | Bidirectional, 2025 | arxiv.org/abs/2510.14296 |
| Corpus synthétique | SIGMOD 2025 Data+AI | dbgroup.cs.tsinghua.edu.cn |
