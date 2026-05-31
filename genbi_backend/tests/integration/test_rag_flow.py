"""
T517 — Tests intégration flux RAG.
Vérifie que feedback good → indexation ChromaDB,
feedback bad → non indexé,
et que le prompt SQL intègre les exemples RAG.
"""
import pytest
from unittest.mock import patch

FEEDBACK = "/api/v1/feedback"

_GOOD_FEEDBACK = {
    "question": "Quel est mon CA en mars 2026 ?",
    "sql_generated": "SELECT SUM(total_amount_fcfa) FROM marts.fct_sales WHERE sale_month=3 AND sale_year=2026",
    "rating": "good",
}

_BAD_FEEDBACK = {
    "question": "Combien de ventes en avril ?",
    "sql_generated": "SELECT COUNT(*) FROM marts.fct_sales WHERE sale_month=4",
    "rating": "bad",
}


@pytest.fixture(autouse=True)
def mock_embed_integration():
    """Remplace _embed par un vecteur déterministe — aucun appel Ollama."""
    def fake_embed(text: str) -> list:
        h = abs(hash(text))
        return [(h >> i & 1) * 1.0 for i in range(64)]

    with patch("core.rag._embed", side_effect=fake_embed):
        yield


def test_feedback_good_indexe_dans_chromadb(client, auth_bourguiba):
    """Feedback good + sql_generated → paire retrouvable via retrieve_examples."""
    from main import app
    from core.rag import retrieve_examples

    r = client.post(FEEDBACK, json=_GOOD_FEEDBACK, headers=auth_bourguiba)
    assert r.status_code == 201

    rag_client = app.state.rag_client
    results = retrieve_examples(rag_client, pharmacy_id=1, question=_GOOD_FEEDBACK["question"])
    assert any(ex["sql"] == _GOOD_FEEDBACK["sql_generated"] for ex in results)


def test_feedback_bad_non_indexe(client, auth_bourguiba):
    """Feedback bad → exemple non indexé dans ChromaDB."""
    from main import app
    from core.rag import retrieve_examples

    r = client.post(FEEDBACK, json=_BAD_FEEDBACK, headers=auth_bourguiba)
    assert r.status_code == 201

    rag_client = app.state.rag_client
    results = retrieve_examples(rag_client, pharmacy_id=1, question=_BAD_FEEDBACK["question"])
    assert _BAD_FEEDBACK["sql_generated"] not in [ex["sql"] for ex in results]


def test_isolation_rag_entre_pharmacies(client, auth_bourguiba):
    """Exemple indexé pour pharma 1 invisible depuis pharma 2."""
    from main import app
    from core.rag import retrieve_examples

    unique_question = "Question unique isolation test pharma"
    unique_sql = "SELECT 42 AS isolation_test"
    client.post(
        FEEDBACK,
        json={"question": unique_question, "sql_generated": unique_sql, "rating": "good"},
        headers=auth_bourguiba,
    )

    rag_client = app.state.rag_client
    results_pharma2 = retrieve_examples(rag_client, pharmacy_id=2, question=unique_question)
    assert all(ex["sql"] != unique_sql for ex in results_pharma2)


def test_prompt_sql_contient_exemples_si_fournis():
    """Le prompt SQL intègre le bloc <examples> quand des exemples sont passés."""
    from core.llm import build_sql_prompt

    examples = [
        {"question": "Mon CA ?", "sql": "SELECT SUM(ca) FROM marts.fct_sales"},
    ]
    prompt = build_sql_prompt(schema="<schema>", question="Question test", examples=examples)
    assert "<examples>" in prompt
    assert "Mon CA ?" in prompt
    assert "SELECT SUM(ca)" in prompt


def test_prompt_sql_sans_exemples_ne_contient_pas_bloc():
    """Sans exemples, le bloc <examples> est absent du prompt."""
    from core.llm import build_sql_prompt

    prompt = build_sql_prompt(schema="<schema>", question="Question test")
    assert "<examples>" not in prompt
