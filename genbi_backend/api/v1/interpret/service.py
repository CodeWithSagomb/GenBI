from core.exceptions import GenBIException
from core.llm import generate_insight


async def interpret(question: str, results: dict) -> str:
    """Génère un insight en français depuis des données structurées."""
    if not results.get("rows"):
        raise GenBIException("Impossible de générer un insight : aucune donnée fournie.")
    return await generate_insight(question, results)
