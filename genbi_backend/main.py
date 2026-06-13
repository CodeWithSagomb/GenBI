from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from core.exceptions import (
    GenBIException, SQLValidationError, LLMTimeoutError, ManifestNotFoundError,
    DatabaseError, AuthError, RateLimitError, ForbiddenError,
)
from core.auth import get_current_pharmacy
from core.middleware import RequestIDMiddleware, LoggingMiddleware, configure_logging
from api.v1.chat.router import router as chat_router
from api.v1.execute.router import router as execute_router
from api.v1.schema.router import router as schema_router
from api.v1.interpret.router import router as interpret_router
from api.v1.query.router import router as query_router
from api.v1.suggestions.router import router as suggestions_router
from api.v1.feedback.router import router as feedback_router
from api.v1.admin.router import router as admin_router
from api.v1.auth.router import router as auth_jwt_router
from api.v1.analyse.router import router as analyse_router


_DEV_JWT_SECRET = "dev_secret_change_in_production"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise manifest + pool DB + ChromaDB au démarrage — libère à l'arrêt."""
    configure_logging()

    import logging
    import chromadb
    from core.dbt_parser import load_manifest, count_models
    from core.database import create_pool, create_write_pool

    if settings.JWT_SECRET_KEY == _DEV_JWT_SECRET:
        logging.getLogger("genbi").warning(
            "⚠️  JWT_SECRET_KEY est la valeur par défaut de développement. "
            "Définir JWT_SECRET_KEY dans genbi_backend/.env avant de déployer en production."
        )

    app.state.manifest = load_manifest(settings.DBT_MANIFEST_PATH)
    app.state.manifest_model_count = count_models(settings.DBT_MANIFEST_PATH)
    app.state.db_pool = create_pool()
    app.state.db_write_pool = create_write_pool()
    app.state.rag_client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)

    # Couche sémantique : charge le catalogue YAML (best-effort)
    try:
        from core.semantic_layer import load_catalog
        app.state.semantic_catalog = load_catalog(settings.SEMANTIC_CATALOG_PATH)
        logging.getLogger("genbi").info(
            "Semantic catalog chargé : %d métriques, %d dimensions, %d filtres",
            len(app.state.semantic_catalog.get("metrics", [])),
            len(app.state.semantic_catalog.get("dimensions", [])),
            len(app.state.semantic_catalog.get("filtres", [])),
        )
    except Exception as _exc:
        app.state.semantic_catalog = None
        logging.getLogger("genbi").warning("Semantic catalog non chargé (best-effort): %s", _exc)

    # Seed RAG : injecte les exemples golden dans ChromaDB si collections vides (best-effort)
    try:
        from core.rag import seed_collection
        from tests.benchmark.golden_questions import GOLDEN_QUESTIONS
        _log = logging.getLogger("genbi")
        for _pid in [1, 2, 3]:
            _n = seed_collection(app.state.rag_client, _pid, GOLDEN_QUESTIONS)
            if _n > 0:
                _log.info("RAG seed: %d exemples indexés pour pharmacie %d", _n, _pid)
    except Exception as _exc:
        logging.getLogger("genbi").warning("RAG seed échoué (best-effort): %s", _exc)

    yield

    app.state.db_pool.closeall()
    app.state.db_write_pool.closeall()


app = FastAPI(
    title="GenBI API",
    description="Business Intelligence Générative pour pharmacies — SQL en langage naturel, LLM local.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# Middleware — exécutés dans l'ordre inverse d'ajout (LIFO)
# Résultat : RequestID → Logging → CORSMiddleware → handler
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)


# Exception handlers — domain exceptions → codes HTTP
@app.exception_handler(SQLValidationError)
async def sql_validation_handler(_: Request, exc: SQLValidationError):
    return JSONResponse(status_code=400, content={"error": str(exc)})

@app.exception_handler(LLMTimeoutError)
async def llm_timeout_handler(_: Request, exc: LLMTimeoutError):
    return JSONResponse(status_code=504, content={"error": str(exc)})

@app.exception_handler(ManifestNotFoundError)
async def manifest_handler(_: Request, exc: ManifestNotFoundError):
    return JSONResponse(status_code=503, content={"error": str(exc)})

@app.exception_handler(DatabaseError)
async def database_handler(_: Request, exc: DatabaseError):
    return JSONResponse(status_code=503, content={"error": str(exc)})

@app.exception_handler(AuthError)
async def auth_handler(_: Request, exc: AuthError):
    return JSONResponse(status_code=401, content={"error": str(exc)})

@app.exception_handler(ForbiddenError)
async def forbidden_handler(_: Request, exc: ForbiddenError):
    return JSONResponse(status_code=403, content={"error": str(exc)})

@app.exception_handler(RateLimitError)
async def rate_limit_handler(_: Request, exc: RateLimitError):
    return JSONResponse(status_code=429, content={"error": str(exc)})

@app.exception_handler(GenBIException)
async def genbi_handler(_: Request, exc: GenBIException):
    return JSONResponse(status_code=400, content={"error": str(exc)})


app.include_router(chat_router)
app.include_router(execute_router)
app.include_router(schema_router)
app.include_router(interpret_router)
app.include_router(query_router)
app.include_router(suggestions_router)
app.include_router(feedback_router)
app.include_router(admin_router)
app.include_router(auth_jwt_router)
app.include_router(analyse_router)


@app.get("/", include_in_schema=False)
def root():
    return {"status": "online", "docs": "/docs"}


@app.get("/api/v1/ping", tags=["auth"])
def ping(pharmacy_id: int = Depends(get_current_pharmacy)):
    """Endpoint léger — vérifie l'authentification sans toucher à la DB."""
    return {"pharmacy_id": pharmacy_id}


@app.get("/api/health", tags=["health"])
def health_check(request: Request):
    import urllib.request as _urllib

    # DB + RLS
    pool = getattr(request.app.state, "db_pool", None)
    db_status = "not_initialized"
    rls_status = "unknown"
    if pool:
        conn = None
        try:
            conn = pool.getconn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.execute(
                    "SELECT COUNT(*) FROM pg_policies WHERE tablename = 'fct_sales'"
                )
                rls_status = "active" if cur.fetchone()[0] > 0 else "inactive"
            db_status = "connected"
        except Exception:
            db_status = "error"
        finally:
            if conn:
                pool.putconn(conn)

    # Ollama
    try:
        with _urllib.urlopen(
            settings.OLLAMA_BASE_URL.replace("host.docker.internal", "localhost") + "/api/tags",
            timeout=3,
        ) as resp:
            ollama_status = "connected" if resp.status == 200 else "error"
    except Exception:
        try:
            with _urllib.urlopen(settings.OLLAMA_BASE_URL + "/api/tags", timeout=3) as resp:
                ollama_status = "connected" if resp.status == 200 else "error"
        except Exception:
            ollama_status = "unreachable"

    manifest = getattr(request.app.state, "manifest", None)
    model_count = getattr(request.app.state, "manifest_model_count", 0)

    return {
        "status": "healthy",
        "db": db_status,
        "ollama": ollama_status,
        "manifest": "loaded" if manifest else "not_loaded",
        "manifest_models": model_count,
        "rls": rls_status,
    }
