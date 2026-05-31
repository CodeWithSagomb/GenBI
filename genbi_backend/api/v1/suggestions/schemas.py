from pydantic import BaseModel


class SuggestionsResponse(BaseModel):
    suggestions: list[str]
