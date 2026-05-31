from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from core.exceptions import (
    GenBIException, SQLValidationError, LLMTimeoutError, ManifestNotFoundError,
    DatabaseError, AuthError, RateLimitError,
)
from core.auth import get_current_pharmacy
from core.middleware import RequestIDMiddleware, LoggingMiddleware, configure_logging
from api.v1.chat.router import router as chat_router
from api.v1.execute.router import router as execute_router
from api.v1.schema.router import router as schema_router
from api.v1.interpret.router import router as interpret_router
from api.v1.query.router import router as query_router
from api.v1.suggestions.router import router as suggestions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise manifest + pool DB au démarrage — libère à l'arrêt."""
    configure_logging()

    from core.dbt_parser import load_manifest, count_models
    from core.database import create_pool

    app.state.manifest = load_manifest(settings.DBT_MANIFEST_PATH)
    app.state.manifest_model_count = count_models(settings.DBT_MANIFEST_PATH)
    app.state.db_pool = create_pool()

    yield

    app.state.db_pool.closeall()


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


@app.get("/", include_in_schema=False)
def root():
    return {"status": "online", "docs": "/docs"}


@app.get("/api/v1/ping", tags=["auth"])
def ping(pharmacy_id: int = Depends(get_current_pharmacy)):
    """Endpoint léger — vérifie l'authentification sans toucher à la DB."""
    return {"pharmacy_id": pharmacy_id}


@app.get("/api/health", tags=["health"])
def health_check(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    manifest = getattr(request.app.state, "manifest", None)
    model_count = getattr(request.app.state, "manifest_model_count", 0)
    return {
        "status": "healthy",
        "db": "connected" if pool else "not_initialized",
        "manifest": "loaded" if manifest else "not_loaded",
        "manifest_models": model_count,
    }
