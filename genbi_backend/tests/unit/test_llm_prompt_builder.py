"""Tests unitaires — core/llm.py (prompt builder + timeout).

Les appels Ollama réels ne sont pas testés ici (lents, réseau requis).
On teste : construction des prompts + gestion du timeout.
"""
import pytest
from unittest.mock import patch

from core.llm import build_sql_prompt, build_insight_prompt, generate_sql, _clean_sql
from core.exceptions import LLMTimeoutError


# ── Prompt SQL ────────────────────────────────────────────────────────────────

def test_prompt_sql_contient_schema_avant_question():
    schema = "Table: marts.fct_sales\n  - total_amount_fcfa: Montant total"
    question = "Quel est mon CA ?"
    prompt = build_sql_prompt(schema, question)

    idx_schema   = prompt.index(schema)
    idx_question = prompt.index(question)
    assert idx_schema < idx_question, "Le schéma doit apparaître avant la question"


def test_prompt_sql_utilise_balises_xml():
    prompt = build_sql_prompt("schema", "question")
    assert "<schema_dbt>" in prompt
    assert "</schema_dbt>" in prompt
    assert "<question>" in prompt
    assert "</question>" in prompt


# ── Prompt Insight ────────────────────────────────────────────────────────────

def test_prompt_insight_contient_les_donnees():
    results = {"columns": ["CA"], "rows": [[45000]]}
    prompt = build_insight_prompt("Quel est mon CA ?", results)
    assert "45000" in prompt
    assert "CA" in prompt


def test_insight_prompt_inclut_annotations():
    """Vérifie que build_insight_prompt injecte les annotations de type de colonne."""
    results = {"columns": ["total_sales"], "rows": [[389]]}
    prompt = build_insight_prompt("Combien de ventes ?", results)
    assert "NOMBRE DE TRANSACTIONS" in prompt
    assert "389" in prompt


# ── _clean_sql ────────────────────────────────────────────────────────────────

def test_clean_sql_retire_bloc_markdown_sql():
    raw = "```sql\nSELECT 1\n```"
    assert _clean_sql(raw) == "SELECT 1"


def test_clean_sql_retire_bloc_markdown_sans_langage():
    raw = "```\nSELECT 1\n```"
    assert _clean_sql(raw) == "SELECT 1"


def test_clean_sql_retire_point_virgule_final():
    raw = "SELECT 1;"
    assert _clean_sql(raw) == "SELECT 1"


def test_clean_sql_passe_sql_propre_intact():
    sql = "SELECT id FROM marts.fct_sales"
    assert _clean_sql(sql) == sql


# ── Timeout ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_timeout_leve_llm_timeout_error():
    """Vérifie que TimeoutError (litellm ou asyncio) → LLMTimeoutError."""
    async def raises_timeout(*args, **kwargs):
        raise TimeoutError("simulated timeout")

    with patch("litellm.acompletion", new=raises_timeout):
        with pytest.raises(LLMTimeoutError):
            await generate_sql("schema", "question")
