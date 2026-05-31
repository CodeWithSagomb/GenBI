from fastapi import Request
from core.llm import generate_sql


async def chat(question: str, request: Request) -> str:
    """Génère un SELECT SQL depuis une question en langage naturel."""
    schema: str = request.app.state.manifest
    return await generate_sql(schema, question)
