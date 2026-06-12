from pydantic import BaseModel, Field


class AnalyseRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class SubAnalysis(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[list]
    row_count: int
    insight: str


class AnalyseResponse(BaseModel):
    question: str
    is_compound: bool
    sub_analyses: list[SubAnalysis]
