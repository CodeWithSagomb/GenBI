from fastapi import APIRouter, Depends, Request

from core.auth import get_current_pharmacy
from core.database import get_write_conn
from api.v1.feedback.schemas import FeedbackRequest, FeedbackResponse
from api.v1.feedback.service import insert_feedback

router = APIRouter(
    prefix="/api/v1/feedback",
    tags=["feedback"],
)


@router.post("", response_model=FeedbackResponse, status_code=201)
def feedback_endpoint(
    body: FeedbackRequest,
    request: Request,
    pharmacy_id: int = Depends(get_current_pharmacy),
    conn=Depends(get_write_conn),
):
    result = insert_feedback(body, pharmacy_id, conn, request)
    return FeedbackResponse(**result)
