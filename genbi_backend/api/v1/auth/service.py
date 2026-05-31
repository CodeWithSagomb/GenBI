from core.exceptions import AuthError
from core.security import verify_password, create_access_token, decode_access_token


def login(email: str, password: str, conn) -> dict:
    """Vérifie email+password → retourne un JWT signé."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT user_id, password_hash, pharmacy_id, role FROM raw.users WHERE email = %s",
            (email,),
        )
        row = cur.fetchone()

    if row is None or not verify_password(password, row[1]):
        raise AuthError("Email ou mot de passe incorrect.")

    user_id, _, pharmacy_id, role = row
    token = create_access_token({
        "sub": email,
        "user_id": user_id,
        "pharmacy_id": pharmacy_id,
        "role": role,
    })
    return {"access_token": token, "token_type": "bearer"}


def me(token: str) -> dict:
    """Décode le JWT et retourne les infos utilisateur."""
    payload = decode_access_token(token)
    return {
        "user_id": payload["user_id"],
        "email": payload["sub"],
        "pharmacy_id": payload.get("pharmacy_id"),
        "role": payload["role"],
    }


def refresh(token: str) -> dict:
    """Vérifie le token courant et émet un nouveau JWT."""
    payload = decode_access_token(token)
    new_token = create_access_token({
        "sub": payload["sub"],
        "user_id": payload["user_id"],
        "pharmacy_id": payload.get("pharmacy_id"),
        "role": payload["role"],
    })
    return {"access_token": new_token, "token_type": "bearer"}
