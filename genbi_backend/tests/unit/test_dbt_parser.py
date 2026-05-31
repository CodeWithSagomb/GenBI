"""Tests unitaires — core/dbt_parser.py"""
import tempfile
import os
from core.exceptions import ManifestNotFoundError


MANIFEST = "/app/dbt_project/target/manifest.json"


def _load(path: str = MANIFEST) -> str:
    from core.dbt_parser import load_manifest
    load_manifest.cache_clear()
    return load_manifest(path)


def test_parse_manifest_retourne_string_non_vide():
    result = _load()
    assert isinstance(result, str)
    assert len(result) > 0


def test_parse_manifest_contient_marts_fct_sales():
    result = _load()
    assert "marts.fct_sales" in result


def test_parse_manifest_contient_descriptions_colonnes():
    result = _load()
    # Toutes les colonnes documentées doivent apparaître
    assert "total_amount_fcfa" in result
    assert "pharmacy_id" in result


def test_parse_manifest_exclut_schema_raw():
    result = _load()
    assert "Table: raw." not in result


def test_manifest_absent_leve_manifest_not_found_error():
    from core.dbt_parser import load_manifest
    load_manifest.cache_clear()
    import pytest
    with pytest.raises(ManifestNotFoundError):
        load_manifest("/chemin/inexistant/manifest.json")


def test_manifest_corrompu_leve_erreur_explicite():
    from core.dbt_parser import load_manifest
    import pytest
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        f.write("{ ceci n'est pas du JSON valide")
        tmp_path = f.name
    try:
        load_manifest.cache_clear()
        with pytest.raises(ManifestNotFoundError, match="corrompu"):
            load_manifest(tmp_path)
    finally:
        os.unlink(tmp_path)
        load_manifest.cache_clear()
