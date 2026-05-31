from fastapi import APIRouter, Depends

from core.auth import get_current_pharmacy
from api.v1.interpret.schemas import InterpretRequest, InterpretResponse
from api.v1.interpret.service import interpret

router = APIRouter(
    prefix="/api/v1/interpret",
    tags=["interpret"],
    dependencies=[Depends(get_current_pharmacy)],
)


@router.post("", response_model=InterpretResponse)
async def interpret_endpoint(body: InterpretRequest):
    insight = await interpret(body.question, body.results)
    return InterpretResponse(insight=insight)
