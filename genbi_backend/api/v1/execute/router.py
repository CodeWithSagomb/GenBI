from fastapi import APIRouter, Depends

from core.auth import get_current_pharmacy
from core.database import get_db_conn
from core.pagination import PageParams
from api.v1.execute.schemas import SQLRequest, QueryResult
from api.v1.execute.service import execute_sql

router = APIRouter(
    prefix="/api/v1/execute",
    tags=["execute"],
    dependencies=[Depends(get_current_pharmacy)],
)


@router.post("", response_model=QueryResult)
def execute_endpoint(
    body: SQLRequest,
    page: PageParams = Depends(),
    conn=Depends(get_db_conn),
):
    result = execute_sql(body.sql, conn, page)
    return QueryResult(**result)
