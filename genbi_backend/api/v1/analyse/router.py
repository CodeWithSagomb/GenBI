from fastapi import APIRouter, Depends, Request

from core.auth import get_current_pharmacy
from api.v1.analyse.schemas import AnalyseRequest, AnalyseResponse
from api.v1.analyse.service import analyse_pipeline

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
    result = await analyse_pipeline(body.question, schema, pool, pharmacy_id, rag_client=rag_client, semantic_catalog=semantic_catalog, schema_embeddings=schema_embeddings, conversation_history=conversation_history or None)
    return AnalyseResponse(**result)
