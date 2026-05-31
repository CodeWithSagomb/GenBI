from fastapi import Request


def get_schema(request: Request) -> str:
    """Retourne le schéma dbt formaté depuis l'état de l'application."""
    return request.app.state.manifest
