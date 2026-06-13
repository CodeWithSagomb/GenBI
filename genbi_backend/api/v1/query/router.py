from fastapi import APIRouter, Depends, Request

from core.auth import get_current_pharmacy
from core.database import get_db_conn
from core.pagination import PageParams
from api.v1.query.schemas import QueryRequest, QueryResponse
from api.v1.query.service import query_pipeline

router = APIRouter(
    prefix="/api/v1/query",
    tags=["query"],
    dependencies=[Depends(get_current_pharmacy)],
)


@router.post("", response_model=QueryResponse)
async def query_endpoint(
    body: QueryRequest,
    request: Request,
    page: PageParams = Depends(),
    conn=Depends(get_db_conn),
    pharmacy_id: int = Depends(get_current_pharmacy),
):
    schema: str = request.app.state.manifest
    rag_client = getattr(request.app.state, "rag_client", None)
    semantic_catalog = getattr(request.app.state, "semantic_catalog", None)
    result = await query_pipeline(body.question, schema, conn, page, rag_client=rag_client, pharmacy_id=pharmacy_id, semantic_catalog=semantic_catalog)
    return QueryResponse(**result)
