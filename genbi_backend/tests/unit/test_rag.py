"""
T512 — Tests unitaires core/rag.py
Écrits AVANT l'implémentation (TDD red → green).
"""
import pytest
import chromadb
from unittest.mock import patch

from core.rag import get_collection, index_example, retrieve_examples


@pytest.fixture
def chroma_client():
    """Client ChromaDB en mémoire — isolé par test, aucun I/O disque."""
    return chromadb.EphemeralClient()


@pytest.fixture(autouse=True)
def mock_embed():
    """Remplace _embed par un vecteur déterministe (aucun appel réseau Ollama)."""
    def fake_embed(text: str) -> list:
        h = abs(hash(text))
        return [(h >> i & 1) * 1.0 for i in range(64)]

    with patch("core.rag._embed", side_effect=fake_embed):
        yield


# ─── get_collection ───────────────────────────────────────────────────────────

def test_get_collection_retourne_une_collection(chroma_client):
    col = get_collection(chroma_client, pharmacy_id=1)
    assert col is not None
    assert col.name == "pharmacy_1"


def test_get_collection_isole_par_pharmacie(chroma_client):
    col1 = get_collection(chroma_client, pharmacy_id=1)
    col2 = get_collection(chroma_client, pharmacy_id=2)
    assert col1.name != col2.name


# ─── index_example + retrieve_examples ────────────────────────────────────────

def test_index_puis_retrieve_retrouve_lexemple(chroma_client):
    index_example(chroma_client, pharmacy_id=1, question="Mon CA ?", sql="SELECT SUM(ca) FROM marts.fct_sales")
    results = retrieve_examples(chroma_client, pharmacy_id=1, question="Mon chiffre d'affaires ?", n=3)
    assert len(results) == 1
    assert results[0]["question"] == "Mon CA ?"
    assert "SELECT SUM(ca)" in results[0]["sql"]


def test_retrieve_retourne_liste_vide_si_collection_vide(chroma_client):
    results = retrieve_examples(chroma_client, pharmacy_id=99, question="Question test", n=3)
    assert results == []


def test_isolation_pharmacie_index_invisible_depuis_autre_pharmacie(chroma_client):
    index_example(chroma_client, pharmacy_id=1, question="Ventes Bourguiba ?", sql="SELECT 1")
    results = retrieve_examples(chroma_client, pharmacy_id=2, question="Ventes Bourguiba ?", n=3)
    assert results == []


def test_retrieve_n_limite_le_nombre_de_resultats(chroma_client):
    for i in range(5):
        index_example(chroma_client, pharmacy_id=1, question=f"Question {i}", sql=f"SELECT {i}")
    results = retrieve_examples(chroma_client, pharmacy_id=1, question="Question", n=2)
    assert len(results) <= 2


# ─── Comportement best-effort ─────────────────────────────────────────────────

def test_embedding_indisponible_retourne_liste_vide(chroma_client):
    """Si _embed échoue, retrieve_examples retourne [] sans lever d'exception."""
    with patch("core.rag._embed", side_effect=Exception("Ollama indisponible")):
        results = retrieve_examples(chroma_client, pharmacy_id=1, question="Test", n=3)
    assert results == []


def test_index_indisponible_ne_leve_pas_dexception(chroma_client):
    """index_example est best-effort : une erreur embedding ne doit pas propager."""
    with patch("core.rag._embed", side_effect=Exception("Ollama indisponible")):
        index_example(chroma_client, pharmacy_id=1, question="Test", sql="SELECT 1")
