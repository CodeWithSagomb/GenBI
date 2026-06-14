"""Tests unitaires — core/llm.py (prompt builder + timeout + versionnage).

Les appels Ollama réels ne sont pas testés ici (lents, réseau requis).
On teste : construction des prompts, gestion du timeout, versionnage v1/v2.
"""
import pytest
from unittest.mock import patch

from core.llm import build_sql_prompt, build_insight_prompt, build_repair_prompt, generate_sql, _clean_sql, load_prompt
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


# ── Versionnage prompt (T614) ─────────────────────────────────────────────────

def test_load_prompt_v1_contient_regles_de_base():
    """v1 est chargeable et contient la règle ruptures."""
    prompt = load_prompt("v1_sql_generation")
    assert "fct_missed_sales" in prompt
    assert "sale_month" in prompt


def test_load_prompt_v2_contient_correctifs_cibles():
    """v2 contient les 4 corrections : therapeutic_class, product_category, seed ruptures, groupement."""
    prompt = load_prompt("v2_sql_generation")
    assert "therapeutic_class" in prompt
    assert "therapeutic_group" in prompt      # mentionné pour dire de NE PAS l'utiliser
    assert "product_category" in prompt
    assert "'Médicament'" in prompt
    assert "'Parapharmacie'" in prompt
    assert "GROUP BY pd.product_category" in prompt


# ── semantic_context ─────────────────────────────────────────────────────────

def test_prompt_v2_avec_semantic_context_contient_bloc():
    ctx = "<semantic_context>\nTermes détectés :\n- Chiffre d'affaires = SUM(total_amount_fcfa)\n</semantic_context>\n"
    prompt = build_sql_prompt("schema", "question", semantic_context=ctx)
    assert "<semantic_context>" in prompt
    assert "Chiffre d'affaires" in prompt


def test_prompt_v2_sans_semantic_context_pas_de_bloc():
    prompt = build_sql_prompt("schema", "question", semantic_context="")
    assert "<semantic_context>" not in prompt


def test_semantic_context_positionne_avant_question():
    ctx = "<semantic_context>\nTermes détectés :\n- CA\n</semantic_context>\n"
    prompt = build_sql_prompt("schema", "ma question", semantic_context=ctx)
    assert prompt.index("<semantic_context>") < prompt.index("ma question")


def test_prompt_v1_avec_semantic_context_ne_plante_pas():
    """v1 n'a pas {semantic_context} — l'injection conditionnelle doit éviter KeyError."""
    with patch("core.llm.settings") as mock_settings:
        mock_settings.SQL_PROMPT_VERSION = "v1_sql_generation"
        prompt = build_sql_prompt("schema", "question", semantic_context="<semantic_context>test</semantic_context>")
    assert "question" in prompt
    assert "<semantic_context>" not in prompt


# ── Repair prompt (Phase 1 — MARS-SQL) ───────────────────────────────────────

def test_repair_prompt_contient_failed_sql_et_error():
    """Le prompt de réparation doit exposer le SQL raté et le message d'erreur au LLM."""
    failed = "SELECT * FROM fct_sales"
    error = 'relation "fct_sales" does not exist'
    prompt = build_repair_prompt("schema", "Quel est mon CA ?", failed, error)
    assert failed in prompt
    assert error in prompt
    assert "<failed_sql>" in prompt
    assert "<error>" in prompt


def test_repair_prompt_contient_schema_et_question():
    prompt = build_repair_prompt("mon_schema", "ma question", "SELECT 1", "erreur")
    assert "mon_schema" in prompt
    assert "ma question" in prompt


# ── build_sql_prompt version configurable ─────────────────────────────────────

def test_build_sql_prompt_utilise_version_configurable():
    """build_sql_prompt doit charger la version définie dans settings.SQL_PROMPT_VERSION."""
    with patch("core.llm.settings") as mock_settings:
        mock_settings.SQL_PROMPT_VERSION = "v1_sql_generation"
        prompt_v1 = build_sql_prompt("schema_test", "question_test")

    with patch("core.llm.settings") as mock_settings:
        mock_settings.SQL_PROMPT_VERSION = "v2_sql_generation"
        prompt_v2 = build_sql_prompt("schema_test", "question_test")

    # v2 doit contenir des éléments absents de v1
    assert "GROUP BY pd.product_category" not in prompt_v1
    assert "GROUP BY pd.product_category" in prompt_v2
