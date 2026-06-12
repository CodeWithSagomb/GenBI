"""Couche sémantique GenBI — résolution des termes métier du pharmacien.

Trois opérations :
  load_catalog(path)              → dict (charge le YAML)
  resolve_semantics(question, catalog) → str (bloc XML ou "")
  _normalize(text)                → str (minuscules + sans accents)

Le bloc <semantic_context> est injecté dans le prompt SQL pour ancrer
le LLM sur les définitions exactes détectées dans la question.
"""
import unicodedata
from pathlib import Path

import yaml

_DEFAULT_CATALOG_PATH = Path(__file__).parent / "semantic_catalog.yaml"


def load_catalog(path: str | Path | None = None) -> dict:
    """Charge le catalogue sémantique depuis un fichier YAML.

    Retourne un dict avec les clés 'metrics', 'dimensions', 'filtres'.
    Lève FileNotFoundError si le fichier est absent.
    """
    p = Path(path) if path else _DEFAULT_CATALOG_PATH
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _normalize(text: str) -> str:
    """Minuscules + suppression des accents pour matching insensible."""
    lowered = text.lower()
    nfkd = unicodedata.normalize("NFKD", lowered)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _format_entry(entry: dict) -> str:
    """Formate une entrée du catalogue en une ligne lisible pour le LLM."""
    label = entry["label"]

    if "sql" in entry:
        line = f"- {label} = {entry['sql']}"
        unite = entry.get("unite", "")
        table = entry.get("table", "")
        if unite:
            line += f" [{unite}]"
        if table:
            line += f" — table : {table}"
        filtre = entry.get("filtre", "")
        if filtre:
            line += f" (filtre : {filtre})"
        return line

    if "colonnes" in entry:
        cols = " / ".join(f"{t} → {c}" for t, c in entry["colonnes"].items())
        return f"- {label} → GROUP BY {cols}"

    if "colonne" in entry:
        jointure = entry.get("jointure", "")
        line = f"- {label} → {entry['colonne']}"
        if jointure:
            line += f" (via {jointure})"
        return line

    return f"- {label}"


def resolve_semantics(question: str, catalog: dict | None) -> str:
    """Détecte les termes métier dans la question et retourne un bloc XML.

    Retourne "" si catalog est None/vide ou si aucun terme n'est reconnu.
    Le bloc est injecté dans le prompt SQL avant les règles critiques.
    """
    if not catalog:
        return ""

    q_norm = _normalize(question)
    matches: list[dict] = []
    seen_ids: set[str] = set()

    all_entries = (
        catalog.get("metrics", [])
        + catalog.get("dimensions", [])
        + catalog.get("filtres", [])
    )

    for entry in all_entries:
        entry_id = entry.get("id", "")
        if entry_id in seen_ids:
            continue
        synonymes = entry.get("synonymes", [])
        # Synonymes de moins de 3 caractères ignorés — trop ambigus en français
        if any(_normalize(syn) in q_norm for syn in synonymes if len(_normalize(syn)) >= 3):
            matches.append(entry)
            seen_ids.add(entry_id)

    if not matches:
        return ""

    lines = [_format_entry(m) for m in matches]
    body = "\n".join(lines)
    return f"<semantic_context>\nTermes détectés :\n{body}\n</semantic_context>\n"
