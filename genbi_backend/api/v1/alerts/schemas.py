from pydantic import BaseModel


class Alert(BaseModel):
    id: str
    severity: str          # "danger" | "warning" | "info"
    title: str
    columns: list[str]
    rows: list[list]
    row_count: int
    insight: str           # vide si row_count == 0


class AlertsResponse(BaseModel):
    alerts: list[Alert]
