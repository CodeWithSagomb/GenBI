from collections import defaultdict
from time import time
from fastapi import Header
from config import settings
from core.exceptions import AuthError, RateLimitError

RATE_LIMIT = 10   # requêtes max
RATE_WINDOW = 60  # secondes

# Rate limiting en mémoire : {api_key: [timestamps]}
_request_log: dict[str, list[float]] = defaultdict(list)


def _get_api_keys() -> dict[str, int]:
    """Construit le mapping clé → pharmacy_id depuis les settings."""
    return {
        settings.API_KEY_BOURGUIBA: 1,
        settings.API_KEY_ALMADIES:  2,
        settings.API_KEY_NATION:    3,
    }


def _check_rate_limit(api_key: str) -> None:
    now = time()
    _request_log[api_key] = [t for t in _request_log[api_key] if now - t < RATE_WINDOW]
    if len(_request_log[api_key]) >= RATE_LIMIT:
        raise RateLimitError(
            f"Limite de {RATE_LIMIT} requêtes/minute atteinte. Réessayez dans quelques secondes."
        )
    _request_log[api_key].append(now)


def get_current_pharmacy(x_api_key: str = Header(...)) -> int:
    """Valide la clé API et retourne le pharmacy_id associé."""
    pharmacy_id = _get_api_keys().get(x_api_key)
    if pharmacy_id is None:
        raise AuthError("Clé API invalide ou manquante.")
    _check_rate_limit(x_api_key)
    return pharmacy_id
