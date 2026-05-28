# Tasks : 002-backend-api

**Input** : `specs/002-backend-api/spec.md`
**Constitution** : `.specify/memory/constitution.md`
**Prérequis** : `dbt_project/target/manifest.json` généré (Phase 2 terminée)

---

## Stratégie de test

**Règle absolue :** les tests du `sql_validator` sont écrits **avant** l'implémentation (TDD) — c'est le composant de sécurité le plus critique du système.

Pour les autres modules, les tests sont écrits **en même temps** que le code, dans la même PR.

```
genbi_backend/
├── tests/
│   ├── conftest.py              ← client de test FastAPI + fixtures DB
│   ├── unit/
│   │   ├── test_sql_validator.py   ← TDD — écrire en premier
│   │   └── test_dbt_parser.py
│   └── integration/
│       ├── test_chat_endpoint.py
│       ├── test_execute_endpoint.py
│       └── test_schema_endpoint.py
```

**Commande d'exécution :**
```bash
docker exec genbi_backend pytest tests/ -v --tb=short
```

---

## Format : `[ID] [P?] [US?] Description`
- `[P]` = peut s'exécuter en parallèle
- `[USN]` = User Story N
- `[T]` = tâche de test (écrite avant ou avec l'implémentation)

---

## Phase 1 : Setup infrastructure de test

- [ ] T001 Créer `genbi_backend/tests/__init__.py` et `genbi_backend/tests/unit/__init__.py` et `genbi_backend/tests/integration/__init__.py`
- [ ] T002 Créer `genbi_backend/tests/conftest.py` :
  - `client` fixture : `TestClient(app)` de FastAPI
  - `readonly_db` fixture : connexion `genbi_readonly` vers PostgreSQL (tests d'intégration)
  - `manifest_path` fixture : chemin vers `dbt_project/target/manifest.json`
- [ ] T003 Ajouter `pytest` et `httpx` dans `requirements.txt`
- [ ] T004 Valider : `docker exec genbi_backend pytest tests/ --collect-only` — collecte sans erreur

**Checkpoint** : infrastructure de test opérationnelle

---

## Phase 2 : Structure du backend (domaines)

- [ ] T005 Créer la structure de dossiers `api/v1/` avec `__init__.py` :
  ```
  genbi_backend/
  ├── api/v1/chat/      (router.py, schemas.py, service.py)
  ├── api/v1/execute/   (router.py, schemas.py, service.py)
  ├── api/v1/schema/    (router.py, service.py)
  └── core/             (dbt_parser.py, sql_validator.py, llm.py)
  ```
- [ ] T006 Mettre à jour `main.py` pour inclure les routers `v1`

**Checkpoint** : structure en place, `make up` toujours vert

---

## Phase 3 : sql_validator — TDD (User Story 2) 🔒

> **Écrire les tests AVANT l'implémentation — ils doivent échouer d'abord.**

### Tests sql_validator (écrire en premier)

- [ ] T007 [T] [US2] Créer `tests/unit/test_sql_validator.py` avec les cas suivants :
  ```python
  # Cas autorisés
  test_select_simple_accepte()
  test_select_with_join_accepte()
  test_select_with_subquery_accepte()
  test_select_marts_schema_accepte()

  # Cas refusés — sécurité critique
  test_delete_rejete()
  test_drop_table_rejete()
  test_insert_rejete()
  test_update_rejete()
  test_truncate_rejete()
  test_create_table_rejete()

  # Cas limites
  test_sql_vide_rejete()
  test_sql_invalide_leve_erreur_parseable()
  test_injection_semicolon_double_statement_rejete()
  test_select_suivi_de_drop_rejete()
  ```
- [ ] T008 Vérifier que tous les tests **échouent** (`pytest tests/unit/test_sql_validator.py` → FAILED) — le module n'existe pas encore

### Implémentation sql_validator

- [ ] T009 [US2] Créer `core/sql_validator.py` :
  - Parser SQLGlot en dialecte `postgres`
  - Whitelist exclusive : seul `exp.Select` autorisé
  - Détection des statements multiples (injection par `;`)
  - Lever `ValueError` avec message explicite en français
- [ ] T010 Vérifier que tous les tests **passent** (`pytest tests/unit/test_sql_validator.py` → PASSED)

**Checkpoint US2-sécurité** : 100% des tests sql_validator verts avant de continuer

---

## Phase 4 : dbt_parser — US3

### Tests dbt_parser

- [ ] T011 [T] [US3] Créer `tests/unit/test_dbt_parser.py` :
  ```python
  test_parse_manifest_retourne_string_non_vide()
  test_parse_manifest_contient_marts_fct_sales()
  test_parse_manifest_contient_descriptions_colonnes()
  test_parse_manifest_exclut_schema_raw()      # raw ne doit pas être exposé à l'IA
  test_manifest_absent_leve_file_not_found()
  test_manifest_corrompu_leve_erreur_explicite()
  ```

### Implémentation dbt_parser

- [ ] T012 [US3] Créer `core/dbt_parser.py` :
  - Lecture du `manifest.json` avec `lru_cache` (chargé une seule fois)
  - Filtrage : uniquement les modèles des schémas `staging` et `marts`
  - Formatage : `Table: marts.fct_sales\n  Description: ...\n  - colonne: description`
  - Gestion d'erreur si fichier absent ou JSON invalide
- [ ] T013 [US3] Créer `api/v1/schema/router.py` — `GET /api/v1/schema`
- [ ] T014 Vérifier que les tests dbt_parser passent : `pytest tests/unit/test_dbt_parser.py`

**Checkpoint US3** : le schéma est lisible via l'API

---

## Phase 5 : LLM client — US1

- [ ] T015 Créer `core/llm.py` — client LiteLLM vers Ollama :
  - Modèle : `ollama/qwen2.5-coder:7b` (via `OLLAMA_BASE_URL`)
  - `temperature=0.0` (déterminisme SQL)
  - Timeout configurable (défaut : 30s)
  - Prompt builder : `<dbt_schema>` + `<user_question>` (données avant question)
- [ ] T016 [T] Créer `tests/unit/test_llm_prompt_builder.py` :
  ```python
  test_prompt_contient_schema_avant_question()
  test_prompt_utilise_balises_xml()
  test_timeout_leve_erreur_explicite()
  ```

---

## Phase 6 : Endpoints complets — US1 & US2

### Tests d'intégration (écrire avec l'implémentation)

- [ ] T017 [T] [US1] Créer `tests/integration/test_chat_endpoint.py` :
  ```python
  test_chat_retourne_200_avec_sql()           # champ 'sql' présent dans réponse
  test_chat_question_vide_retourne_400()
  test_chat_retourne_json_structure()         # champs: sql, question, schema_used
  ```
- [ ] T018 [T] [US2] Créer `tests/integration/test_execute_endpoint.py` :
  ```python
  test_execute_select_retourne_resultats()
  test_execute_delete_retourne_400()
  test_execute_drop_retourne_400()
  test_execute_sql_invalide_retourne_400()
  test_execute_utilise_user_readonly()        # vérifier que genbi_readonly est utilisé
  test_execute_retourne_colonnes_et_lignes()  # format JSON structuré
  ```
- [ ] T019 [T] [US3] Créer `tests/integration/test_schema_endpoint.py` :
  ```python
  test_schema_retourne_200()
  test_schema_contient_marts()
  test_schema_exclut_raw()   # raw ne doit jamais être exposé
  ```

### Implémentation endpoints

- [ ] T020 [US1] Créer `api/v1/chat/schemas.py` — `ChatRequest(question: str)`, `ChatResponse(sql: str, question: str)`
- [ ] T021 [US1] Créer `api/v1/chat/service.py` — orchestration : dbt_parser → prompt → llm → sql
- [ ] T022 [US1] Créer `api/v1/chat/router.py` — `POST /api/v1/chat`
- [ ] T023 [US2] Créer `api/v1/execute/schemas.py` — `SQLRequest(sql: str)`, `QueryResult(columns, rows, row_count)`
- [ ] T024 [US2] Créer `api/v1/execute/service.py` — validate_sql → connexion readonly → exécution → JSON
- [ ] T025 [US2] Créer `api/v1/execute/router.py` — `POST /api/v1/execute`
- [ ] T026 Mettre à jour `GET /api/health` pour inclure : DB accessible, Ollama accessible, manifest.json chargé
- [ ] T027 Exécuter tous les tests : `pytest tests/ -v` — cible : **0 échec**

**Checkpoint Final** : `pytest tests/ -v` → 100% vert

---

## Phase 7 : Validation manuelle end-to-end

- [ ] T028 [US1] Envoyer une vraie question via `curl POST /api/v1/chat` et vérifier le SQL généré
- [ ] T029 [US2] Exécuter le SQL retourné via `POST /api/v1/execute` et vérifier les résultats
- [ ] T030 [US1][CS-004] Mesurer le temps de réponse — cible : < 15 secondes sur matériel local

---

## Dépendances & ordre d'exécution

```
Phase 1 (Setup test)
    ↓
Phase 2 (Structure)
    ↓
Phase 3 (sql_validator — TDD) ← commencer ici, tests en premier
    ↓
Phase 4 (dbt_parser)       ← en parallèle possible avec Phase 5
Phase 5 (LLM client)       ←
    ↓
Phase 6 (Endpoints complets)
    ↓
Phase 7 (Validation manuelle)
```

## Couverture de test cible

| Module | Type | Cas testés | Priorité |
|---|---|---|---|
| `sql_validator.py` | Unitaire TDD | 13 cas (4 OK + 6 refus + 3 limites) | 🔴 Critique |
| `dbt_parser.py` | Unitaire | 6 cas | 🟡 Important |
| `llm.py` (prompt builder) | Unitaire | 3 cas | 🟡 Important |
| `POST /api/v1/chat` | Intégration | 3 cas | 🟡 Important |
| `POST /api/v1/execute` | Intégration | 6 cas | 🔴 Critique |
| `GET /api/v1/schema` | Intégration | 3 cas | 🟢 Standard |
