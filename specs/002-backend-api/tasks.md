# Tasks : 002-backend-api

**Input** : `specs/002-backend-api/spec.md`
**Constitution** : `.specify/memory/constitution.md`
**Prérequis** : `dbt_project/target/manifest.json` généré (Phase 2 terminée)
**Mise à jour** : 2026-05-29 — intégration best practices FastAPI (lifespan, domain exceptions, pool, prompts versionnés)

---

## Stratégie de test

**Règle absolue :** les tests du `sql_validator` sont écrits **avant** l'implémentation (TDD).
Pour tous les autres modules : tests écrits **en même temps** que le code.

**Pattern de test :** `app.dependency_overrides` pour mock DB — jamais de monkeypatch global.

```
genbi_backend/
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_sql_validator.py      ← TDD — écrire en premier, 13 cas
│   │   ├── test_dbt_parser.py
│   │   └── test_llm_prompt_builder.py
│   └── integration/
│       ├── test_chat_endpoint.py
│       ├── test_execute_endpoint.py   ← inclut test current_user=genbi_readonly
│       ├── test_schema_endpoint.py
│       ├── test_query_endpoint.py
│       ├── test_interpret_endpoint.py
│       └── test_suggestions_endpoint.py
```

**Commande :**
```bash
docker exec genbi_backend pytest tests/ -v --tb=short
```

---

## Format : `[ID] [P?] [US?] Description`
- `[P]` = peut s'exécuter en parallèle avec d'autres
- `[USN]` = User Story N
- `[T]` = tâche de test

---

## Phase 1 : Infrastructure de test

- [ ] T001 Créer `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
- [ ] T002 Créer `tests/conftest.py` :
  - `client` fixture : `TestClient(app)` avec `dependency_overrides` pour DB
  - `readonly_db` fixture : connexion `genbi_readonly` réelle (tests d'intégration)
  - `manifest_path` fixture : chemin vers `dbt_project/target/manifest.json`
- [ ] T003 Ajouter dans `requirements.txt` : `pytest`, `httpx`, `pytest-asyncio`
- [ ] T004 Valider : `docker exec genbi_backend pytest tests/ --collect-only` — 0 erreur

**Checkpoint** : infrastructure de test opérationnelle

---

## Phase 2 : Structure du backend

- [ ] T005 Créer la structure complète avec `__init__.py` :
  ```
  genbi_backend/
  ├── api/v1/
  │   ├── chat/       (router.py, schemas.py, service.py)
  │   ├── execute/    (router.py, schemas.py, service.py)
  │   ├── schema/     (router.py, service.py)
  │   ├── query/      (router.py, schemas.py, service.py)
  │   ├── interpret/  (router.py, schemas.py, service.py)
  │   ├── suggestions/(router.py, service.py)
  │   └── feedback/   (router.py, schemas.py, service.py)
  └── core/
      ├── sql_validator.py
      ├── dbt_parser.py
      ├── llm.py
      ├── database.py         ← ThreadedConnectionPool
      ├── exceptions.py       ← hiérarchie d'exceptions domaine
      └── prompts/
          └── v1_sql_generation.txt   ← template prompt versionné
  ```
- [ ] T006 Créer `core/exceptions.py` :
  ```python
  class GenBIException(Exception): pass
  class SQLValidationError(GenBIException): pass
  class LLMTimeoutError(GenBIException): pass
  class ManifestNotFoundError(GenBIException): pass
  class DatabaseError(GenBIException): pass
  ```
- [ ] T007 Créer `core/database.py` — `ThreadedConnectionPool(minconn=2, maxconn=10, user="genbi_readonly")`
- [ ] T008 Mettre à jour `main.py` :
  - `lifespan` : charger `manifest.json` + initialiser pool au démarrage, fermer pool à l'arrêt
  - `exception_handler` pour chaque exception domaine → code HTTP approprié
  - Inclure tous les routers `v1`
- [ ] T009 Créer `core/prompts/v1_sql_generation.txt` :
  ```
  <schema_dbt>
  {schema}
  </schema_dbt>

  <question>
  {question}
  </question>

  Génère uniquement un SELECT SQL valide PostgreSQL. Rien d'autre.
  ```

**Checkpoint** : `make up` toujours vert, structure en place

---

## Phase 3 : sql_validator — TDD 🔒

> **Écrire les tests AVANT l'implémentation — ils doivent échouer d'abord.**

### Tests (écrire en premier)

- [ ] T010 [T] [US2] Créer `tests/unit/test_sql_validator.py` — 13 cas :
  ```python
  # Autorisés
  test_select_simple_accepte()
  test_select_with_join_accepte()
  test_select_with_subquery_accepte()
  test_select_marts_schema_accepte()
  # Refusés
  test_delete_rejete()
  test_drop_table_rejete()
  test_insert_rejete()
  test_update_rejete()
  test_truncate_rejete()
  test_create_table_rejete()
  # Limites
  test_sql_vide_rejete()
  test_injection_semicolon_double_statement_rejete()
  test_select_suivi_de_drop_rejete()
  ```
- [ ] T011 Vérifier que tous les tests **échouent** (module absent) → FAILED attendu

### Implémentation

- [ ] T012 [US2] Créer `core/sql_validator.py` :
  - Parser SQLGlot dialecte `postgres`
  - Whitelist exclusive : `exp.Select` uniquement
  - Détection statements multiples (injection `;`)
  - Lève `SQLValidationError` (pas HTTPException) avec message en français
- [ ] T013 Vérifier : `pytest tests/unit/test_sql_validator.py` → **13 PASSED**

**Checkpoint US2** : 100% vert avant de continuer

---

## Phase 4 : dbt_parser — US3

### Tests

- [ ] T014 [T] [US3] Créer `tests/unit/test_dbt_parser.py` :
  ```python
  test_parse_manifest_retourne_string_non_vide()
  test_parse_manifest_contient_marts_fct_sales()
  test_parse_manifest_contient_descriptions_colonnes()
  test_parse_manifest_exclut_schema_raw()
  test_manifest_absent_leve_manifest_not_found_error()
  test_manifest_corrompu_leve_erreur_explicite()
  ```

### Implémentation

- [ ] T015 [US3] Créer `core/dbt_parser.py` :
  - Lecture `manifest.json` avec `lru_cache` (chargé une seule fois via lifespan)
  - Filtrer : uniquement `staging.*` et `marts.*` — raw exclu
  - Format : `Table: marts.fct_sales\n  Description: ...\n  - colonne: description`
  - Lève `ManifestNotFoundError` si fichier absent
- [ ] T016 [US3] Créer `api/v1/schema/router.py` — `GET /api/v1/schema`
- [ ] T017 Créer `tests/integration/test_schema_endpoint.py` :
  ```python
  test_schema_retourne_200()
  test_schema_contient_marts()
  test_schema_exclut_raw()
  ```
- [ ] T018 `pytest tests/unit/test_dbt_parser.py tests/integration/test_schema_endpoint.py` → PASSED

**Checkpoint US3** : schéma lisible via API

---

## Phase 5 : LLM client — US1

- [ ] T019 Créer `core/llm.py` — client LiteLLM vers Ollama :
  - Modèle : `ollama/qwen2.5-coder:7b`
  - `temperature=0.0` — déterminisme SQL obligatoire
  - Timeout : `asyncio.timeout(30)` → lève `LLMTimeoutError`
  - `build_sql_prompt(schema: str, question: str) -> str` — lit `core/prompts/v1_sql_generation.txt`
  - `build_insight_prompt(question: str, results: dict) -> str` — prompt séparé pour l'insight
- [ ] T020 [T] Créer `tests/unit/test_llm_prompt_builder.py` :
  ```python
  test_prompt_sql_contient_schema_avant_question()
  test_prompt_sql_utilise_balises_xml()
  test_prompt_insight_contient_les_donnees()
  test_timeout_leve_llm_timeout_error()
  ```
- [ ] T021 `pytest tests/unit/test_llm_prompt_builder.py` → PASSED

---

## Phase 6 : Endpoint /chat — US1

- [ ] T022 [US1] Créer `api/v1/chat/schemas.py` :
  ```python
  class ChatRequest(BaseModel):
      question: str = Field(..., min_length=3, max_length=500)
      @field_validator("question")
      def strip_and_validate(cls, v): ...
  class ChatResponse(BaseModel):
      question: str
      sql: str
      schema_used: bool = True
  ```
- [ ] T023 [US1] Créer `api/v1/chat/service.py` — `generate_sql(question) -> str`
- [ ] T024 [US1] Créer `api/v1/chat/router.py` — `POST /api/v1/chat`
- [ ] T025 [T] [US1] Créer `tests/integration/test_chat_endpoint.py` :
  ```python
  test_chat_retourne_200_avec_sql()
  test_chat_question_vide_retourne_422()
  test_chat_retourne_json_structure()
  test_chat_llm_timeout_retourne_504()
  ```
- [ ] T026 `pytest tests/integration/test_chat_endpoint.py` → PASSED

---

## Phase 7 : Endpoint /execute — US2

- [ ] T027 [US2] Créer `api/v1/execute/schemas.py` :
  ```python
  class SQLRequest(BaseModel):
      sql: str = Field(..., min_length=6)
  class QueryResult(BaseModel):
      columns: list[str]
      rows: list[list]
      row_count: int
  ```
- [ ] T028 [US2] Créer `api/v1/execute/service.py` — `validate_sql → get_conn → execute → QueryResult`
- [ ] T029 [US2] Créer `api/v1/execute/router.py` — `POST /api/v1/execute`
- [ ] T030 [T] [US2] Créer `tests/integration/test_execute_endpoint.py` :
  ```python
  test_execute_select_retourne_resultats()
  test_execute_delete_retourne_400()
  test_execute_drop_retourne_400()
  test_execute_sql_invalide_retourne_400()
  test_execute_utilise_user_readonly()     # SELECT current_user = 'genbi_readonly'
  test_execute_retourne_colonnes_et_lignes()
  ```
- [ ] T031 `pytest tests/integration/test_execute_endpoint.py` → PASSED

---

## Phase 8 : Endpoint /interpret — US5

- [ ] T032 [US5] Créer `api/v1/interpret/schemas.py` :
  ```python
  class InterpretRequest(BaseModel):
      question: str
      results: dict  # {columns, rows}
  class InterpretResponse(BaseModel):
      insight: str
  ```
- [ ] T033 [US5] Créer `api/v1/interpret/service.py` — `generate_insight(question, results) -> str`
- [ ] T034 [US5] Créer `api/v1/interpret/router.py` — `POST /api/v1/interpret`
- [ ] T035 [T] Créer `tests/integration/test_interpret_endpoint.py` :
  ```python
  test_interpret_retourne_200_avec_insight()
  test_interpret_results_vide_retourne_400()
  test_interpret_insight_est_string_non_vide()
  ```
- [ ] T036 `pytest tests/integration/test_interpret_endpoint.py` → PASSED

---

## Phase 9 : Endpoint /query — US4 (pipeline complet)

- [ ] T037 [US4] Créer `api/v1/query/schemas.py` :
  ```python
  class QueryRequest(BaseModel):
      question: str = Field(..., min_length=3, max_length=500)
  class QueryResponse(BaseModel):
      question: str
      sql: str
      columns: list[str]
      rows: list[list]
      row_count: int
      insight: str
  ```
- [ ] T038 [US4] Créer `api/v1/query/service.py` — orchestre : dbt_parser → llm → sql_validator → execute → llm (insight)
- [ ] T039 [US4] Créer `api/v1/query/router.py` — `POST /api/v1/query`
- [ ] T040 [T] [US4] Créer `tests/integration/test_query_endpoint.py` :
  ```python
  test_query_retourne_sql_donnees_et_insight()
  test_query_sql_invalide_retourne_400_avant_execution()
  test_query_question_vide_retourne_422()
  test_query_structure_complete()   # tous les champs présents
  ```
- [ ] T041 `pytest tests/integration/test_query_endpoint.py` → PASSED

---

## Phase 10 : Endpoint /suggestions — US6

- [ ] T042 [US6] Créer `api/v1/suggestions/service.py` — liste statique de questions pharmacien Dakar :
  ```python
  SUGGESTIONS = [
      "Quel est mon CA total ce mois ?",
      "Quels sont mes 5 produits les plus vendus ?",
      "Quelles ruptures de stock ai-je eu cette semaine ?",
      "Quel est mon taux de ventes en tiers-payant ?",
      "Quels lots expirent dans les 30 prochains jours ?",
      ...
  ]
  ```
- [ ] T043 [US6] Créer `api/v1/suggestions/router.py` — `GET /api/v1/suggestions`
- [ ] T044 [T] Créer `tests/integration/test_suggestions_endpoint.py` :
  ```python
  test_suggestions_retourne_200()
  test_suggestions_liste_non_vide()
  test_suggestions_contient_au_moins_5_questions()
  ```

---

## Phase 11 : Endpoint /feedback — US7

- [ ] T045 [US7] Créer `api/v1/feedback/schemas.py` :
  ```python
  class FeedbackRequest(BaseModel):
      question: str
      sql: str
      rating: Literal["good", "bad"]
      comment: str | None = None
  ```
- [ ] T046 [US7] Créer `api/v1/feedback/service.py` — insert dans `raw.feedback` via genbi_readonly... NON — via user `postgres` (seul cas d'écriture autorisée via user dédié)
- [ ] T047 [US7] Créer `api/v1/feedback/router.py` — `POST /api/v1/feedback` → 201

---

## Phase 12 : Health check enrichi + validation finale

- [ ] T048 Mettre à jour `GET /api/health` :
  ```json
  {
    "status": "healthy",
    "db": "connected",
    "ollama": "connected",
    "manifest": "loaded",
    "manifest_models": 19
  }
  ```
- [ ] T049 Exécuter tous les tests : `pytest tests/ -v` → **0 échec**
- [ ] T050 Validation manuelle E2E :
  - `curl POST /api/v1/chat` avec vraie question → SQL valide
  - `curl POST /api/v1/execute` avec le SQL retourné → données réelles
  - `curl POST /api/v1/query` → réponse complète < 30 secondes

---

## Dépendances & ordre d'exécution

```
Phase 1 (Setup test)
    ↓
Phase 2 (Structure + lifespan + exceptions + database + prompts)
    ↓
Phase 3 (sql_validator — TDD) 🔒 ← tests en premier
    ↓
Phase 4 (dbt_parser)    ←─ en parallèle possible ─→  Phase 5 (llm)
    ↓                                                      ↓
Phase 6 (/chat) ──────────────────────────────────────────┘
    ↓
Phase 7 (/execute)
    ↓
Phase 8 (/interpret)
    ↓
Phase 9 (/query)  ← dépend de chat + execute + interpret
    ↓
Phase 10 (/suggestions) ←─ en parallèle ─→ Phase 11 (/feedback)
    ↓
Phase 12 (Health + validation finale)
```

---

## Couverture de test cible

| Module | Type | Cas | Priorité |
|---|---|---|---|
| `sql_validator.py` | Unitaire TDD | 13 | 🔴 Critique |
| `dbt_parser.py` | Unitaire | 6 | 🟡 Important |
| `llm.py` prompt builder | Unitaire | 4 | 🟡 Important |
| `POST /api/v1/chat` | Intégration | 4 | 🟡 Important |
| `POST /api/v1/execute` | Intégration | 6 | 🔴 Critique |
| `GET /api/v1/schema` | Intégration | 3 | 🟢 Standard |
| `POST /api/v1/query` | Intégration | 4 | 🔴 Critique |
| `POST /api/v1/interpret` | Intégration | 3 | 🟡 Important |
| `GET /api/v1/suggestions` | Intégration | 3 | 🟢 Standard |
| **Total** | | **46 cas** | |

---

## Notes d'implémentation critiques

1. **Lifespan** — manifest + pool chargés **une seule fois** au démarrage. Jamais dans les routes.
2. **Domain exceptions** — `sql_validator`, `dbt_parser`, `llm` lèvent des exceptions domaine. `main.py` les traduit en HTTP.
3. **temperature=0.0** — obligatoire sur tous les appels LLM pour SQL. L'insight peut être à 0.3.
4. **genbi_readonly** — toutes les lectures. Seul `/feedback` écrit (user dédié `genbi_write` à créer si besoin).
5. **ThreadedConnectionPool** — psycopg2 sync suffit. Le goulot est le LLM (~10s), pas la DB (~50ms).
6. **Prompts versionnés** — `core/prompts/v1_sql_generation.txt`. Changer le prompt = changer de fichier, pas de code.
