import os
from fastapi import Header
from core.exceptions import AuthError, RateLimitError
from collections import defaultdict
from time import time

# Chargé depuis les variables d'environnement — jamais hardcodé en production
_API_KEYS: dict[str, int] = {
    os.getenv("API_KEY_BOURGUIBA", "pk_bourguiba_dev"): 1,
    os.getenv("API_KEY_ALMADIES",  "pk_almadies_dev"):  2,
    os.getenv("API_KEY_NATION",    "pk_nation_dev"):    3,
}

# Rate limiting en mémoire : {api_key: [timestamps]}
_request_log: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 10   # requêtes
RATE_WINDOW = 60  # secondes


def _check_rate_limit(api_key: str) -> None:
    now = time()
    timestamps = _request_log[api_key]
    # Garder uniquement les timestamps dans la fenêtre glissante
    _request_log[api_key] = [t for t in timestamps if now - t < RATE_WINDOW]
    if len(_request_log[api_key]) >= RATE_LIMIT:
        raise RateLimitError(
            f"Limite de {RATE_LIMIT} requêtes par minute atteinte. Réessayez dans quelques secondes."
        )
    _request_log[api_key].append(now)


def get_current_pharmacy(x_api_key: str = Header(...)) -> int:
    """Valide la clé API et retourne le pharmacy_id associé."""
    pharmacy_id = _API_KEYS.get(x_api_key)
    if pharmacy_id is None:
        raise AuthError("Clé API invalide ou manquante.")
    _check_rate_limit(x_api_key)
    return pharmacy_id
