"""Tests unitaires — reload_manifest() dans core/dbt_parser.py."""
from core.dbt_parser import reload_manifest, load_manifest


def test_reload_vide_le_cache(tmp_path):
    """Après reload, le cache est vidé puis rechargé depuis le disque."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"nodes": {}, "metadata": {}}', encoding="utf-8")
    path = str(manifest)

    # Premier appel — mise en cache
    load_manifest(path)
    assert load_manifest.cache_info().currsize == 1

    # cache_clear() remet les compteurs à zéro ; reload relit le fichier
    reload_manifest(path)
    info = load_manifest.cache_info()
    assert info.currsize == 1   # rechargé
    assert info.misses == 1     # exactement 1 miss depuis le clear (reload l'a relu)
    assert info.hits == 0       # aucun hit depuis le clear


def test_reload_retourne_texte_et_count(tmp_path):
    """reload_manifest retourne (manifest_text, model_count)."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"nodes": {}, "metadata": {}}', encoding="utf-8")
    path = str(manifest)

    text, count = reload_manifest(path)
    assert isinstance(text, str)
    assert isinstance(count, int)
    assert count == 0  # manifest vide → 0 modèles
