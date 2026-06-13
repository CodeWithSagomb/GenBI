"""T607 — Tests unitaires core/rag.seed_collection."""
import pytest
import chromadb
from unittest.mock import patch

from core.rag import seed_collection, retrieve_examples


@pytest.fixture
def chroma_client():
    return chromadb.EphemeralClient()


@pytest.fixture(autouse=True)
def mock_embed():
    def fake_embed(text: str) -> list:
        h = abs(hash(text))
        return [(h >> i & 1) * 1.0 for i in range(64)]

    with patch("core.rag._embed", side_effect=fake_embed):
        yield


SAMPLE_EXAMPLES = [
    {"question": "Quel est mon CA total ?",     "golden_sql": "SELECT SUM(total_amount_fcfa) FROM marts.fct_sales"},
    {"question": "Combien de ventes en mars ?", "golden_sql": "SELECT COUNT(*) FROM marts.fct_sales WHERE sale_month = 3"},
    {"question": "Top 5 produits vendus ?",     "golden_sql": "SELECT pd.commercial_name FROM marts.dim_products pd LIMIT 5"},
]

# Chaque test utilise un pharmacy_id distinct pour éviter les collisions
# entre instances EphemeralClient dans le même process.


def test_seed_collection_vide_indexe_tous_les_exemples(chroma_client):
    n = seed_collection(chroma_client, pharmacy_id=10, examples=SAMPLE_EXAMPLES)
    assert n == len(SAMPLE_EXAMPLES)


def test_seed_collection_idempotent_retourne_count(chroma_client):
    """seed_collection est idempotent : un second appel upsert les mêmes exemples sans erreur."""
    seed_collection(chroma_client, pharmacy_id=20, examples=SAMPLE_EXAMPLES)
    n = seed_collection(chroma_client, pharmacy_id=20, examples=SAMPLE_EXAMPLES)
    assert n == len(SAMPLE_EXAMPLES)


def test_seed_collection_exemples_retrouvables_apres_seed(chroma_client):
    seed_collection(chroma_client, pharmacy_id=30, examples=SAMPLE_EXAMPLES)
    results = retrieve_examples(chroma_client, pharmacy_id=30, question="CA total de la pharmacie ?", n=3)
    assert len(results) > 0
    sqls = [r["sql"] for r in results]
    assert any("total_amount_fcfa" in s for s in sqls)


def test_seed_collection_isole_par_pharmacie(chroma_client):
    seed_collection(chroma_client, pharmacy_id=40, examples=SAMPLE_EXAMPLES)
    results = retrieve_examples(chroma_client, pharmacy_id=41, question="CA total ?", n=3)
    assert results == []


def test_seed_collection_best_effort_continue_sur_erreur(chroma_client):
    """Si un exemple échoue en interne (embed error), seed continue et retourne les autres."""
    call_count = 0

    def flaky_embed(text: str) -> list:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("embed error simulée")
        h = abs(hash(text))
        return [(h >> i & 1) * 1.0 for i in range(64)]

    with patch("core.rag._embed", side_effect=flaky_embed):
        n = seed_collection(chroma_client, pharmacy_id=50, examples=SAMPLE_EXAMPLES)

    # La fonction ne plante pas et traite tous les exemples (index_example est best-effort)
    assert n >= len(SAMPLE_EXAMPLES) - 1
