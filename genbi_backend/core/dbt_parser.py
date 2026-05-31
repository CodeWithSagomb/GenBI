import json
from functools import lru_cache
from pathlib import Path

from core.exceptions import ManifestNotFoundError

# Schémas jamais exposés au LLM
_EXCLUDED_SCHEMAS = {"raw"}


@lru_cache(maxsize=1)
def load_manifest(manifest_path: str) -> str:
    """Lit manifest.json et retourne le schéma formaté pour le prompt LLM.

    Chargé une seule fois (lru_cache). Relancer le processus pour recharger.
    Lève ManifestNotFoundError si le fichier est absent ou corrompu.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise ManifestNotFoundError(
            f"manifest.json introuvable : {manifest_path}. Lancer 'dbt docs generate'."
        )
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        raise ManifestNotFoundError(f"manifest.json corrompu : {e}") from e

    return _format_for_llm(manifest)


def _format_for_llm(manifest: dict) -> str:
    """Formate les modèles staging+marts en texte lisible par le LLM."""
    nodes = manifest.get("nodes", {})
    lines: list[str] = []

    for key, node in sorted(nodes.items()):
        if not key.startswith("model."):
            continue
        schema = node.get("schema", "")
        if schema in _EXCLUDED_SCHEMAS:
            continue

        name = node.get("name", "")
        description = node.get("description", "").strip()
        columns = node.get("columns", {})

        lines.append(f"Table: {schema}.{name}")
        if description:
            lines.append(f"  Description: {description}")
        for col_name, col_info in columns.items():
            col_desc = col_info.get("description", "").strip()
            if col_desc:
                lines.append(f"  - {col_name}: {col_desc}")
        lines.append("")

    return "\n".join(lines)


def reload_manifest(manifest_path: str) -> tuple:
    """Vide le cache lru_cache et recharge le manifest depuis le disque.

    À appeler après chaque `dbt run` pour que le backend voie le nouveau schéma
    sans redémarrage du container.

    Retourne (manifest_text, model_count).
    """
    load_manifest.cache_clear()
    text = load_manifest(manifest_path)
    count = count_models(manifest_path)
    return text, count


def count_models(manifest_path: str) -> int:
    """Retourne le nombre de modèles exposés (staging + marts, sans raw)."""
    path = Path(manifest_path)
    if not path.exists():
        return 0
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
        nodes = manifest.get("nodes", {})
        return sum(
            1 for k, v in nodes.items()
            if k.startswith("model.") and v.get("schema", "") not in _EXCLUDED_SCHEMAS
        )
    except Exception:
        return 0
