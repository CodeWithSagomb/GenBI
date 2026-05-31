from fastapi import Request
from core.llm import generate_sql
from core.rag import retrieve_examples


async def chat(question: str, pharmacy_id: int, request: Request) -> str:
    """Génère un SELECT SQL depuis une question en langage naturel.

    Enrichit le prompt avec les exemples RAG les plus proches (best-effort).
    """
    schema: str = request.app.state.manifest
    rag_client = getattr(request.app.state, "rag_client", None)

    examples: list = []
    if rag_client is not None:
        examples = retrieve_examples(rag_client, pharmacy_id, question, n=3)

    return await generate_sql(schema, question, examples)
