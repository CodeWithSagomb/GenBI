import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from core.auth import get_current_pharmacy
from core.llm import generate_insight_stream, _replace_millions_fcfa
from api.v1.analyse.schemas import AnalyseRequest, AnalyseResponse
from api.v1.analyse.service import analyse_pipeline, detect_sub_questions, _run_sub_query
from api.v1.query.service import query_pipeline
from core.pagination import PageParams

router = APIRouter(
    prefix="/api/v1/analyse",
    tags=["analyse"],
    dependencies=[Depends(get_current_pharmacy)],
)


@router.post("", response_model=AnalyseResponse)
async def analyse_endpoint(
    body: AnalyseRequest,
    request: Request,
    pharmacy_id: int = Depends(get_current_pharmacy),
):
    schema: str = request.app.state.manifest
    pool = request.app.state.db_pool
    rag_client = getattr(request.app.state, "rag_client", None)
    semantic_catalog = getattr(request.app.state, "semantic_catalog", None)
    schema_embeddings = getattr(request.app.state, "schema_embeddings", None)
    conversation_history = [t.model_dump() for t in body.conversation_history]
    result = await analyse_pipeline(body.question, schema, pool, pharmacy_id, rag_client=rag_client, semantic_catalog=semantic_catalog, schema_embeddings=schema_embeddings, conversation_history=conversation_history or None, language=body.language)
    return AnalyseResponse(**result)


@router.post("/stream")
async def analyse_stream_endpoint(
    body: AnalyseRequest,
    request: Request,
    pharmacy_id: int = Depends(get_current_pharmacy),
):
    """Endpoint streaming SSE : retourne d'abord les données SQL puis stream l'insight token par token.

    Événements SSE :
      {"type": "data",  "sql": "...", "columns": [...], "rows": [...], "viz_hint": "..."}
      {"type": "token", "content": "..."} (répété N fois)
      {"type": "done",  "insight": "..."}  (insight complet post-processé)
      {"type": "error", "message": "..."}  (en cas d'échec)

    Questions composées : pas de streaming (pas d'insight individuel) — redirige vers le pipeline classique.
    """
    schema: str = request.app.state.manifest
    pool = request.app.state.db_pool
    rag_client = getattr(request.app.state, "rag_client", None)
    semantic_catalog = getattr(request.app.state, "semantic_catalog", None)
    schema_embeddings = getattr(request.app.state, "schema_embeddings", None)
    conversation_history = [t.model_dump() for t in body.conversation_history] or None

    # Questions composées : pas d'insight à streamer, on passe par le pipeline normal
    if detect_sub_questions(body.question) is not None:
        result = await analyse_pipeline(
            body.question, schema, pool, pharmacy_id,
            rag_client=rag_client, semantic_catalog=semantic_catalog,
            schema_embeddings=schema_embeddings,
            conversation_history=conversation_history, language=body.language,
        )
        async def _compound_stream():
            yield f"data: {json.dumps({'type': 'compound', 'result': result}, ensure_ascii=False)}\n\n"
        return StreamingResponse(_compound_stream(), media_type="text/event-stream")

    async def _event_stream():
        page = PageParams(limit=100, offset=0)
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SET app.current_pharmacy_id = %s", (pharmacy_id,))
            conn.commit()

            # Phase 1 : SQL + exécution (sans insight)
            data = await query_pipeline(
                body.question, schema, conn, page,
                with_insight=False,
                rag_client=rag_client,
                pharmacy_id=pharmacy_id,
                semantic_catalog=semantic_catalog,
                schema_embeddings=schema_embeddings,
                conversation_history=conversation_history,
                language=body.language,
            )
            yield f"data: {json.dumps({'type': 'data', 'sql': data['sql'], 'columns': data['columns'], 'rows': data['rows'], 'row_count': data['row_count'], 'viz_hint': data['viz_hint']}, ensure_ascii=False)}\n\n"

            # Phase 2 : streaming insight token par token
            if data['rows']:
                results = {"columns": data['columns'], "rows": data['rows']}
                buffer = ""
                async for token in generate_insight_stream(body.question, results, language=body.language):
                    buffer += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
                corrected = _replace_millions_fcfa(buffer.strip())
            else:
                corrected = (
                    "Aucune donnée disponible pour cette période ou cette sélection."
                    if body.language == 'fr'
                    else "No data available for this period or selection."
                )

            yield f"data: {json.dumps({'type': 'done', 'insight': corrected}, ensure_ascii=False)}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"
            conn.rollback()
        finally:
            try:
                with conn.cursor() as cur:
                    cur.execute("RESET app.current_pharmacy_id")
                conn.commit()
            except Exception:
                pass
            pool.putconn(conn)

    return StreamingResponse(_event_stream(), media_type="text/event-stream")
