from fastapi import APIRouter, Depends, Header, HTTPException, Request

from config import settings
from core.dbt_parser import reload_manifest

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _require_admin(x_admin_secret: str = Header(default="")):
    """Vérifie le secret admin. Désactivé si ADMIN_SECRET n'est pas configuré."""
    if not settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Endpoint admin désactivé (ADMIN_SECRET non configuré).")
    if x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Secret admin invalide.")


@router.post("/reload-manifest", dependencies=[Depends(_require_admin)])
def reload_manifest_endpoint(request: Request):
    """Recharge manifest.json sans redémarrer le container.

    À appeler après `dbt run` ou `dbt docs generate`.
    Requiert le header : X-Admin-Secret: <ADMIN_SECRET>
    """
    manifest_text, model_count = reload_manifest(settings.DBT_MANIFEST_PATH)
    request.app.state.manifest = manifest_text
    request.app.state.manifest_model_count = model_count
    return {"status": "reloaded", "manifest_models": model_count}
