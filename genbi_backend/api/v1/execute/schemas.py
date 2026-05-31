from pydantic import BaseModel, Field


class SQLRequest(BaseModel):
    sql: str = Field(min_length=6)


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[list]
    row_count: int
    limit: int
    offset: int
