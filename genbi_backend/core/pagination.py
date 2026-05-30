from pydantic import BaseModel, Field


class PageParams(BaseModel):
    limit: int = Field(100, ge=1, le=500, description="Nombre de lignes max (défaut 100, max 500)")
    offset: int = Field(0, ge=0, description="Décalage pour la pagination")
