# Tasks : 002-backend-api

**Input** : `specs/002-backend-api/spec.md`
**Constitution** : `.specify/memory/constitution.md`
**Prérequis** : `dbt_project/target/manifest.json` généré (Phase 2 terminée)
**Mise à jour** : 2026-05-31 — ✅ PHASE TERMINÉE — 59/59 tests PASS

## ✅ Résultat final

| Métrique | Valeur |
|---|---|
| Tests PASS | **59/59** en 1.11s |
| Endpoints livrés | `/chat` `/execute` `/schema` `/interpret` `/query` `/suggestions` `/feedback` `/health` `/ping` |
| Isolation RLS | Bourguiba 1 617 ventes · Almadies 1 530 ventes · Nation isolée |
| Commits | T001-T015 · T016-T025 · T026-T032 · T033-T037 · T038-T048 · T049-T054 |
| Gotcha clé | `RETURNING` requiert SELECT — `GRANT INSERT,SELECT ON raw.feedback` |

---

---

## Stratégie de test

**Règle absolue :** `sql_validator` en TDD — tests écrits **avant** le code.
**Pattern de test :** `app.dependency_overrides` pour mocker les dépendances — jamais de monkeypatch global.
**Auth dans les tests :** fixture `auth_headers` avec `{"X-API-Key": "pk_test_bourguiba"}` injectée.

```
genbi_backend/
├── tests/
│   ├── conftest.py                     ← fixtures + dependency_overrides
│   ├── unit/
│   │   ├── test_sql_validator.py       ← TDD — 13 cas — écrire en premier
│   │   ├── test_dbt_parser.py
│   │   └── test_llm_prompt_builder.py
│   └── integration/
│       ├── test_auth.py                ← 401, clé inconnue, rate limit
│       ├── test_chat_endpoint.py
│       ├── test_execute_endpoint.py    ← inclut current_user + isolation RLS
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

## Format
- `[P]` = peut s'exécuter en parallèle
- `[USN]` = User Story N
- `[T]` = tâche de test

---

## Phase 1 : Infrastructure de test

- [ ] T001 Créer `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
- [ ] T002 Créer `tests/conftest.py` :
  ```python
  @pytest.fixture
  def client(app):
      # Override DB dependency avec connexion de test
      app.dependency_overrides[get_db_conn] = lambda: test_conn
      return TestClient(app)

  @pytest.fixture
  def auth_headers():
      return {"X-API-Key": "pk_test_bourguiba"}

  @pytest.fixture
  def manifest_path():
      return Path("../dbt_project/target/manifest.json")
  ```
- [ ] T003 Ajouter dans `requirements.txt` : `pytest`, `httpx`, `pytest-asyncio`
- [ ] T004 Valider : `docker exec genbi_backend pytest tests/ --collect-only` — 0 erreur

**Checkpoint** : infrastructure de test opérationnelle

---

## Phase 2 : Structure + socle technique

### Structure des fichiers
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
      ├── auth.py            ← API Key → pharmacy_id
      ├── database.py        ← ThreadedConnectionPool + RLS setter
      ├── exceptions.py      ← hiérarchie d'exceptions domaine
      ├── middleware.py      ← request_id + logging JSON + rate limiting
      ├── pagination.py      ← PageParams schema réutilisable
      ├── sql_validator.py
      ├── dbt_parser.py
      ├── llm.py
      └── prompts/
          ├── v1_sql_generation.txt
          └── v1_insight_generation.txt
  ```

### Exceptions domaine
- [ ] T006 Créer `core/exceptions.py` :
  ```python
  class GenBIException(Exception): pass
  class SQLValidationError(GenBIException): pass
  class LLMTimeoutError(GenBIException): pass
  class ManifestNotFoundError(GenBIException): pass
  class DatabaseError(GenBIException): pass
  class AuthError(GenBIException): pass
  class RateLimitError(GenBIException): pass
  ```

### Auth — API Key + pharmacy_id
- [ ] T007 [US8] Créer `core/auth.py` :
  ```python
  API_KEYS: dict[str, int] = {
      "pk_bourguiba_xxx": 1,   # Pharmacie Bourguiba
      "pk_almadies_xxx":  2,   # Pharmacie des Almadies
      "pk_nation_xxx":    3,   # Pharmacie de la Nation
  }

  def get_current_pharmacy(x_api_key: str = Header(...)) -> int:
      pharmacy_id = API_KEYS.get(x_api_key)
      if pharmacy_id is None:
          raise AuthError("Clé API invalide ou manquante")
      return pharmacy_id
  ```
  Les vraies clés sont dans `.env` (ne jamais les hardcoder en production).

### Base de données + RLS
- [ ] T008 Créer `core/database.py` :
  ```python
  pool = ThreadedConnectionPool(minconn=2, maxconn=10,
      host=settings.DB_HOST, dbname=settings.DB_NAME,
      user="genbi_readonly", password=settings.DB_READONLY_PASSWORD)

  def get_db_conn(pharmacy_id: int = Depends(get_current_pharmacy)):
      conn = pool.getconn()
      try:
          # RLS : PostgreSQL filtre automatiquement par pharmacy_id
          with conn.cursor() as cur:
              cur.execute("SET app.current_pharmacy_id = %s", (pharmacy_id,))
          yield conn
      finally:
          pool.putconn(conn)
  ```
- [ ] T009 [US8] Ajouter les policies RLS PostgreSQL dans `data/postgres-init/init.sql` :
  ```sql
  -- Activer RLS sur les tables marts
  ALTER TABLE marts.fct_sales ENABLE ROW LEVEL SECURITY;
  ALTER TABLE marts.fct_purchases ENABLE ROW LEVEL SECURITY;
  ALTER TABLE marts.fct_missed_sales ENABLE ROW LEVEL SECURITY;
  ALTER TABLE marts.fct_wholesaler_returns ENABLE ROW LEVEL SECURITY;
  ALTER TABLE marts.dim_stocks ENABLE ROW LEVEL SECURITY;

  -- Policy : chaque connexion ne voit que sa pharmacie
  CREATE POLICY pharmacy_isolation ON marts.fct_sales
      USING (pharmacy_id = current_setting('app.current_pharmacy_id')::int);
  -- (répéter pour chaque table avec pharmacy_id)

  -- genbi_readonly respecte la RLS (BYPASSRLS non accordé)
  -- postgres superuser bypass RLS → OK pour dbt
  ```
- [ ] T010 Créer `raw.feedback` et user `genbi_write` dans `init.sql` :
  ```sql
  CREATE TABLE IF NOT EXISTS raw.feedback (
      feedback_id SERIAL PRIMARY KEY,
      pharmacy_id INT NOT NULL,
      question    TEXT NOT NULL,
      sql_generated TEXT,
      rating      VARCHAR(4) CHECK (rating IN ('good', 'bad')),
      comment     TEXT,
      created_at  TIMESTAMP DEFAULT NOW()
  );
  CREATE USER genbi_write WITH PASSWORD 'write_pass_123';
  GRANT INSERT ON raw.feedback TO genbi_write;
  GRANT USAGE ON SEQUENCE raw.feedback_feedback_id_seq TO genbi_write;
  ```

### Middleware
- [ ] T011 Créer `core/middleware.py` :
  ```python
  # 1. Request ID — UUID généré par requête, retourné dans X-Request-ID
  # 2. Logging JSON structuré — request_id, pharmacy_id, method, path, duration_ms, status
  # 3. Rate limiting — dict en mémoire {api_key: [timestamps]}
  #    10 requêtes/minute/clé → lève RateLimitError si dépassé

  class RequestIDMiddleware(BaseHTTPMiddleware):
      async def dispatch(self, request, call_next):
          request_id = str(uuid.uuid4())
          request.state.request_id = request_id
          response = await call_next(request)
          response.headers["X-Request-ID"] = request_id
          return response

  class LoggingMiddleware(BaseHTTPMiddleware):
      async def dispatch(self, request, call_next):
          start = time.time()
          response = await call_next(request)
          logger.info({
              "request_id": request.state.request_id,
              "method": request.method,
              "path": request.url.path,
              "status": response.status_code,
              "duration_ms": round((time.time() - start) * 1000),
          })
          return response
  ```

### Pagination
- [ ] T012 Créer `core/pagination.py` :
  ```python
  class PageParams(BaseModel):
      limit: int = Field(100, ge=1, le=500)
      offset: int = Field(0, ge=0)
  ```

### Prompts versionnés
- [ ] T013 Créer `core/prompts/v1_sql_generation.txt` :
  ```
  Tu es un expert SQL PostgreSQL pour pharmacies au Sénégal.
  Génère UNIQUEMENT un SELECT SQL valide. Aucun autre texte.

  <schema_dbt>
  {schema}
  </schema_dbt>

  <question>
  {question}
  </question>

  Règles : utiliser uniquement les tables du schema_dbt. Ne pas inventer de colonnes.
  ```
- [ ] T014 Créer `core/prompts/v1_insight_generation.txt` :
  ```
  Tu es un assistant BI pour pharmacien à Dakar. Rédige un insight professionnel en français.

  <question>
  {question}
  </question>

  <resultats>
  {results}
  </resultats>

  Rédige 2-3 phrases synthétisant les points clés. Cite des chiffres précis.
  ```

### main.py
- [ ] T015 Mettre à jour `main.py` :
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      app.state.manifest = load_manifest()   # dbt_parser
      app.state.db_pool = create_pool()      # database.py
      yield
      app.state.db_pool.closeall()

  app = FastAPI(lifespan=lifespan)

  # CORS
  app.add_middleware(CORSMiddleware,
      allow_origins=["http://localhost:5173"],
      allow_methods=["*"], allow_headers=["*"])

  # Request ID + Logging
  app.add_middleware(RequestIDMiddleware)
  app.add_middleware(LoggingMiddleware)

  # Exception handlers centralisés
  @app.exception_handler(SQLValidationError)
  async def sql_handler(r, e): return JSONResponse(400, {"error": str(e)})

  @app.exception_handler(LLMTimeoutError)
  async def timeout_handler(r, e): return JSONResponse(504, {"error": str(e)})

  @app.exception_handler(AuthError)
  async def auth_handler(r, e): return JSONResponse(401, {"error": str(e)})

  @app.exception_handler(RateLimitError)
  async def rate_handler(r, e): return JSONResponse(429, {"error": str(e)})
  ```

**Checkpoint** : `make up` toujours vert, middleware actif, RLS en place

---

## Phase 3 : sql_validator — TDD 🔒

> **Écrire les tests AVANT l'implémentation.**

### Tests (écrire en premier)
- [ ] T016 [T] [US2] Créer `tests/unit/test_sql_validator.py` — 13 cas :
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
- [ ] T017 Vérifier que tous les tests **échouent** (module absent) → FAILED attendu

### Implémentation
- [ ] T018 [US2] Créer `core/sql_validator.py` :
  - SQLGlot dialecte `postgres`
  - Whitelist : `exp.Select` uniquement
  - Détection statements multiples (`;`)
  - Lève `SQLValidationError` (jamais HTTPException)
- [ ] T019 Vérifier : `pytest tests/unit/test_sql_validator.py` → **13 PASSED**

### Tests auth
- [ ] T020 [T] [US8] Créer `tests/integration/test_auth.py` :
  ```python
  test_requete_sans_api_key_retourne_401()
  test_api_key_invalide_retourne_401()
  test_api_key_valide_retourne_200()
  test_rate_limit_depasse_retourne_429()
  ```

**Checkpoint US2+US8** : sécurité validée avant de continuer

---

## Phase 4 : dbt_parser — US3

### Tests
- [ ] T021 [T] [US3] Créer `tests/unit/test_dbt_parser.py` :
  ```python
  test_parse_manifest_retourne_string_non_vide()
  test_parse_manifest_contient_marts_fct_sales()
  test_parse_manifest_contient_descriptions_colonnes()
  test_parse_manifest_exclut_schema_raw()
  test_manifest_absent_leve_manifest_not_found_error()
  test_manifest_corrompu_leve_erreur_explicite()
  ```

### Implémentation
- [ ] T022 [US3] Créer `core/dbt_parser.py` :
  - `lru_cache` — chargé une seule fois
  - Filtre : `staging.*` et `marts.*` — raw exclu
  - Format lisible pour le LLM
  - Lève `ManifestNotFoundError` si absent
- [ ] T023 [US3] Créer `api/v1/schema/router.py` — `GET /api/v1/schema`
- [ ] T024 [T] Créer `tests/integration/test_schema_endpoint.py` :
  ```python
  test_schema_retourne_200(auth_headers)
  test_schema_contient_marts(auth_headers)
  test_schema_exclut_raw(auth_headers)
  ```
- [ ] T025 `pytest tests/unit/test_dbt_parser.py tests/integration/test_schema_endpoint.py` → PASSED

**Checkpoint US3** : schéma lisible via API

---

## Phase 5 : LLM client — US1 [P]

- [ ] T026 Créer `core/llm.py` :
  ```python
  async def generate_sql(schema: str, question: str, timeout: int = 30) -> str:
      prompt = load_prompt("v1_sql_generation").format(schema=schema, question=question)
      async with asyncio.timeout(timeout):
          ...  # appel Ollama qwen2.5-coder:7b, temperature=0.0
      # Lève LLMTimeoutError si dépassé

  async def generate_insight(question: str, results: dict, timeout: int = 20) -> str:
      prompt = load_prompt("v1_insight_generation").format(...)
      # temperature=0.3 pour insight (un peu plus naturel)
  ```
- [ ] T027 [T] Créer `tests/unit/test_llm_prompt_builder.py` :
  ```python
  test_prompt_sql_contient_schema_avant_question()
  test_prompt_sql_utilise_balises_xml()
  test_prompt_insight_contient_les_donnees()
  test_timeout_leve_llm_timeout_error()
  ```
- [ ] T028 `pytest tests/unit/test_llm_prompt_builder.py` → PASSED

---

## Phase 6 : Endpoint /chat — US1

- [ ] T029 [US1] Créer `api/v1/chat/schemas.py` :
  ```python
  class ChatRequest(BaseModel):
      question: str = Field(..., min_length=3, max_length=500)
      @field_validator("question")
      def strip_whitespace(cls, v): return v.strip()

  class ChatResponse(BaseModel):
      question: str
      sql: str
      request_id: str
  ```
- [ ] T030 [US1] Créer `api/v1/chat/service.py` et `router.py`
- [ ] T031 [T] Créer `tests/integration/test_chat_endpoint.py` :
  ```python
  test_chat_retourne_200_avec_sql(auth_headers)
  test_chat_question_vide_retourne_422(auth_headers)
  test_chat_sans_auth_retourne_401()
  test_chat_retourne_request_id_dans_header(auth_headers)
  ```
- [ ] T032 `pytest tests/integration/test_chat_endpoint.py` → PASSED

---

## Phase 7 : Endpoint /execute — US2

- [ ] T033 [US2] Créer `api/v1/execute/schemas.py` :
  ```python
  class SQLRequest(BaseModel):
      sql: str = Field(..., min_length=6)

  class QueryResult(BaseModel):
      columns: list[str]
      rows: list[list]
      row_count: int
      page: int
      limit: int
  ```
- [ ] T034 [US2] Créer `api/v1/execute/service.py` : `validate_sql → get_conn (RLS actif) → execute → paginate → QueryResult`
- [ ] T035 [US2] Créer `api/v1/execute/router.py` avec `PageParams` en query params
- [ ] T036 [T] Créer `tests/integration/test_execute_endpoint.py` :
  ```python
  test_execute_select_retourne_resultats(auth_headers)
  test_execute_delete_retourne_400(auth_headers)
  test_execute_drop_retourne_400(auth_headers)
  test_execute_sql_invalide_retourne_400(auth_headers)
  test_execute_utilise_user_readonly(auth_headers)      # SELECT current_user = 'genbi_readonly'
  test_execute_rls_isole_par_pharmacie()                # clé Bourguiba ≠ données Almadies
  test_execute_pagination_limit_respecte(auth_headers)
  ```
- [ ] T037 `pytest tests/integration/test_execute_endpoint.py` → PASSED

**Checkpoint US2+US8** : sécurité + isolation validées

---

## Phase 8 : Endpoint /interpret — US5 [P]

- [ ] T038 [US5] Créer `api/v1/interpret/schemas.py`, `service.py`, `router.py`
- [ ] T039 [T] Créer `tests/integration/test_interpret_endpoint.py` :
  ```python
  test_interpret_retourne_200_avec_insight(auth_headers)
  test_interpret_results_vide_retourne_400(auth_headers)
  test_interpret_insight_est_string_non_vide(auth_headers)
  ```
- [ ] T040 `pytest tests/integration/test_interpret_endpoint.py` → PASSED

---

## Phase 9 : Endpoint /query — US4 (pipeline complet)

- [ ] T041 [US4] Créer `api/v1/query/schemas.py` :
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
      request_id: str
  ```
- [ ] T042 [US4] Créer `api/v1/query/service.py` — orchestre : dbt_parser → llm(SQL) → sql_validator → execute(RLS) → llm(insight)
- [ ] T043 [US4] Créer `api/v1/query/router.py`
- [ ] T044 [T] Créer `tests/integration/test_query_endpoint.py` :
  ```python
  test_query_retourne_sql_donnees_et_insight(auth_headers)
  test_query_sql_invalide_retourne_400_avant_execution(auth_headers)
  test_query_question_vide_retourne_422(auth_headers)
  test_query_structure_complete(auth_headers)
  test_query_sans_auth_retourne_401()
  ```
- [ ] T045 `pytest tests/integration/test_query_endpoint.py` → PASSED

---

## Phase 10 : Endpoints /suggestions + /feedback — US6 & US7 [P]

- [ ] T046 [US6] Créer `api/v1/suggestions/service.py` — liste statique de 10 questions pharmacien Dakar
- [ ] T047 [US6] Créer `api/v1/suggestions/router.py` — `GET /api/v1/suggestions`
- [ ] T048 [T] Créer `tests/integration/test_suggestions_endpoint.py` :
  ```python
  test_suggestions_retourne_200(auth_headers)
  test_suggestions_liste_non_vide(auth_headers)
  test_suggestions_contient_au_moins_5_questions(auth_headers)
  ```
- [ ] T049 [US7] Créer `api/v1/feedback/schemas.py` :
  ```python
  class FeedbackRequest(BaseModel):
      question: str
      sql_generated: str | None = None
      rating: Literal["good", "bad"]
      comment: str | None = None
  ```
- [ ] T050 [US7] Créer `api/v1/feedback/service.py` — connexion `genbi_write` → INSERT `raw.feedback` avec `pharmacy_id` injecté depuis la clé API
- [ ] T051 [US7] Créer `api/v1/feedback/router.py` — `POST /api/v1/feedback` → 201

---

## Phase 11 : Health check enrichi + validation finale

- [ ] T052 Mettre à jour `GET /api/health` :
  ```json
  {
    "status": "healthy",
    "db": "connected",
    "ollama": "connected",
    "manifest": "loaded",
    "manifest_models": 19,
    "rls": "active"
  }
  ```
- [ ] T053 Exécuter tous les tests : `pytest tests/ -v` → **0 échec**
- [ ] T054 Validation manuelle E2E :
  - `curl POST /api/v1/query` clé Bourguiba → CA Bourguiba uniquement
  - `curl POST /api/v1/query` clé Almadies → CA Almadies uniquement
  - Vérifier `X-Request-ID` dans les headers de réponse
  - Vérifier logs JSON dans `docker logs genbi_backend`
  - Mesurer temps de réponse < 30s

---

## Dépendances & ordre d'exécution

```
Phase 1 (Test infra)
    ↓
Phase 2 (Structure + auth + RLS + middleware + pool + prompts)
    ↓
Phase 3 (sql_validator TDD 🔒 + tests auth)
    ↓
Phase 4 (dbt_parser) ←──────────────────────── Phase 5 (llm) [parallèle]
    ↓                                               ↓
Phase 6 (/chat) ────────────────────────────────────┘
    ↓
Phase 7 (/execute)
    ↓
Phase 8 (/interpret) ←────────────── [parallèle possible après Phase 5]
    ↓
Phase 9 (/query — pipeline complet)
    ↓
Phase 10 (/suggestions + /feedback) [parallèle]
    ↓
Phase 11 (Health + E2E)
```

---

## Couverture de test cible

| Module | Type | Cas | Priorité |
|---|---|---|---|
| `sql_validator.py` | Unitaire TDD | 13 | 🔴 Critique |
| `dbt_parser.py` | Unitaire | 6 | 🟡 Important |
| `llm.py` prompt builder | Unitaire | 4 | 🟡 Important |
| Auth (API Key + rate limit) | Intégration | 4 | 🔴 Critique |
| `POST /api/v1/chat` | Intégration | 4 | 🟡 Important |
| `POST /api/v1/execute` | Intégration | 7 | 🔴 Critique |
| `GET /api/v1/schema` | Intégration | 3 | 🟢 Standard |
| `POST /api/v1/query` | Intégration | 5 | 🔴 Critique |
| `POST /api/v1/interpret` | Intégration | 3 | 🟡 Important |
| `GET /api/v1/suggestions` | Intégration | 3 | 🟢 Standard |
| **Total** | | **52 cas** | |

---

## Notes d'implémentation critiques

1. **RLS > filtre applicatif** — l'isolation des pharmacies est garantie par PostgreSQL, pas par `WHERE pharmacy_id = ?` dans le code. Même un LLM qui "oublie" de filtrer est contraint par RLS.
2. **Lifespan** — manifest + pool chargés **une seule fois**. Jamais dans les routes.
3. **Domain exceptions** — les services lèvent `SQLValidationError`, `LLMTimeoutError`, etc. Jamais `HTTPException`. `main.py` traduit.
4. **temperature=0.0 SQL / 0.3 insight** — SQL = déterminisme, insight = naturel.
5. **genbi_readonly** → toutes les lectures. **genbi_write** → uniquement INSERT sur `raw.feedback`.
6. **API Keys dans `.env`** — jamais dans le code source. `core/auth.py` lit `os.environ`.
7. **Pagination** — défaut 100 lignes, max 500. Protège contre les requêtes retournant 50 000 lignes.
8. **Prompts versionnés** — changer `v1_sql_generation.txt` = nouveau comportement LLM sans toucher au code Python.
9. **X-Request-ID** — présent dans chaque réponse, loggué côté backend → traçabilité bout en bout.
10. **Rate limiting en mémoire** — dict `{api_key: [timestamps]}`, suffisant pour MVP mono-instance.
