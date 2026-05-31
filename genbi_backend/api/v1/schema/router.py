from fastapi import APIRouter, Depends, Request

from core.auth import get_current_pharmacy
from api.v1.schema.service import get_schema

router = APIRouter(prefix="/api/v1/schema", tags=["schema"])


@router.get("")
def schema(
    request: Request,
    pharmacy_id: int = Depends(get_current_pharmacy),
):
    """Retourne le schéma dbt (staging + marts) utilisé pour générer le SQL."""
    return {"schema": get_schema(request), "pharmacy_id": pharmacy_id}
