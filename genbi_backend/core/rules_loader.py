"""Charge les règles de configuration YAML au démarrage — singleton.

Fail-fast : si un fichier YAML est absent, vide ou contient un pattern regex invalide,
l'application ne démarre pas (ValueError ou re.error levée pendant _compile()).

Utilisation dans les autres modules :
    from core.rules_loader import rules

    rules.temporal_re.search(question)          # viz_classifier
    rules.reminders["reminders"]               # llm.py
    rules.compiled_patterns                    # analyse/service.py
    rules.semantic["scalar_keywords"]          # semantic_validator.py
"""
import re
from pathlib import Path
from typing import Any

import yaml

_CONFIG_DIR = Path(__file__).parent.parent / "config"


class RulesLoader:
    def __init__(self) -> None:
        self.viz       = self._load("viz_rules.yaml")
        self.reminders = self._load("llm_reminders.yaml")
        self.patterns  = self._load("analysis_patterns.yaml")
        self.semantic  = self._load("semantic_rules.yaml")
        self._compile()

    def _load(self, filename: str) -> dict[str, Any]:
        path = _CONFIG_DIR / filename
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            raise ValueError(f"Config YAML vide ou invalide : {path}")
        return data

    def _compile(self) -> None:
        """Compile toutes les regex — fail-fast si un pattern est invalide."""
        v = self.viz
        self.temporal_re     = re.compile(v["temporal"]["pattern"],     re.IGNORECASE)
        self.temporal_col_re = re.compile(v["temporal"]["col_pattern"],  re.IGNORECASE)
        self.ranking_re      = re.compile(v["ranking"]["pattern"],       re.IGNORECASE)
        self.composition_re  = re.compile(v["composition"]["pattern"],   re.IGNORECASE)
        self.exclude_col_re  = re.compile(v["exclude"]["col_pattern"],   re.IGNORECASE)
        self.compiled_patterns: list[tuple[re.Pattern, list[str]]] = [
            (re.compile(p["pattern"], re.IGNORECASE), p["sub_questions"])
            for p in self.patterns["patterns"]
        ]

    def reload(self) -> None:
        """Hot-reload sans redémarrage Docker. Usage admin uniquement — non thread-safe."""
        self.__init__()


rules = RulesLoader()
