from fastapi import APIRouter, Depends, Request

from core.auth import get_current_pharmacy
from api.v1.chat.schemas import ChatRequest, ChatResponse
from api.v1.chat.service import chat

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat"],
    dependencies=[Depends(get_current_pharmacy)],
)


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    body: ChatRequest,
    request: Request,
    pharmacy_id: int = Depends(get_current_pharmacy),
):
    sql = await chat(body.question, pharmacy_id, request)
    return ChatResponse(question=body.question, sql=sql)
