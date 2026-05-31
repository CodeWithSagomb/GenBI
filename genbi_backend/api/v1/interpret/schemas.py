from pydantic import BaseModel, Field


class InterpretRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    results: dict  # {columns: [...], rows: [[...]]}


class InterpretResponse(BaseModel):
    insight: str
