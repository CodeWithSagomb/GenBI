from fastapi import APIRouter, Depends

from core.auth import get_current_pharmacy
from core.database import get_db_conn
from api.v1.alerts.schemas import AlertsResponse
from api.v1.alerts.service import generate_alerts

router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["alerts"],
    dependencies=[Depends(get_current_pharmacy)],
)


@router.get("", response_model=AlertsResponse)
async def alerts_endpoint(conn=Depends(get_db_conn)):
    alerts = await generate_alerts(conn)
    return AlertsResponse(alerts=alerts)
