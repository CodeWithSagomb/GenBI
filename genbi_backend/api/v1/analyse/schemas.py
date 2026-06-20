import re
from pydantic import BaseModel, Field, field_validator

_SQL_INJECTION_RE = re.compile(
    r'^\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|WITH|MERGE)\b',
    re.IGNORECASE,
)


class ConversationTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class AnalyseRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    conversation_history: list[ConversationTurn] = Field(default_factory=list, max_length=6)

    @field_validator('question')
    @classmethod
    def reject_raw_sql(cls, v: str) -> str:
        if _SQL_INJECTION_RE.match(v):
            raise ValueError(
                "Ce système répond aux questions en langage naturel. "
                "Les requêtes SQL directes ne sont pas acceptées."
            )
        return v


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
