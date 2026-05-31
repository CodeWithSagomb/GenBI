from fastapi import APIRouter, Depends

from core.auth import get_current_pharmacy
from api.v1.suggestions.schemas import SuggestionsResponse
from api.v1.suggestions.service import get_suggestions

router = APIRouter(
    prefix="/api/v1/suggestions",
    tags=["suggestions"],
    dependencies=[Depends(get_current_pharmacy)],
)


@router.get("", response_model=SuggestionsResponse)
def suggestions_endpoint():
    return SuggestionsResponse(suggestions=get_suggestions())
