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
    """Formate les modèles staging+marts en texte compact pour le prompt LLM.

    Format : une ligne par table — `schema.table: col1, col2, col3`
    Les descriptions longues sont omises pour réduire la taille du contexte
    et améliorer la qualité de génération SQL sur les modèles 7b.
    """
    nodes = manifest.get("nodes", {})
    lines: list[str] = []

    for key, node in sorted(nodes.items()):
        if not key.startswith("model."):
            continue
        schema = node.get("schema", "")
        if schema in _EXCLUDED_SCHEMAS:
            continue

        name = node.get("name", "")
        columns = list(node.get("columns", {}).keys())
        col_list = ", ".join(columns) if columns else "(aucune colonne documentée)"
        lines.append(f"{schema}.{name}: {col_list}")

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
