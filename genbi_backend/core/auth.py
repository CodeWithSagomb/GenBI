from collections import defaultdict
from time import time
from typing import Optional
from fastapi import Header
from config import settings
from core.exceptions import AuthError, ForbiddenError, RateLimitError
from core.security import decode_access_token

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


def get_current_pharmacy(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
) -> int:
    """Retourne le pharmacy_id courant.

    Accepte deux modes :
    - JWT  : Authorization: Bearer <token>  (production + Phase 5)
    - X-API-Key : clé statique (dev / rétrocompatibilité tests Phase 3)
    """
    # ── Mode JWT ──────────────────────────────────────────────────────────────
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):]
        payload = decode_access_token(token)  # lève AuthError si invalide
        pharmacy_id = payload.get("pharmacy_id")
        if pharmacy_id is None:
            raise ForbiddenError("Accès réservé aux pharmaciens. Le rôle admin n'a pas accès à cet endpoint.")
        return int(pharmacy_id)

    # ── Mode X-API-Key (dev / backward-compat) ────────────────────────────────
    if not x_api_key:
        raise AuthError("Authentification requise : fournir Authorization: Bearer <token> ou X-API-Key.")
    pharmacy_id = _get_api_keys().get(x_api_key)
    if pharmacy_id is None:
        raise AuthError("Clé API invalide.")
    _check_rate_limit(x_api_key)
    return pharmacy_id


def reset_rate_limit(api_key: Optional[str] = None) -> None:
    """Réinitialise le rate limiter. Réservé aux tests."""
    if api_key:
        _request_log.pop(api_key, None)
    else:
        _request_log.clear()
