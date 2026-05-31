from typing import Literal, Optional
from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    sql_generated: Optional[str] = None
    rating: Literal["good", "bad"]
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    feedback_id: int
    pharmacy_id: int
    created_at: str
