"""Authentication for the login gate.

Reuses the existing `users` table (same user IDs: RARA, AIRAM, …) but authenticates
against a securely hashed `password_hash` column rather than the legacy PowerBuilder
password obfuscation (which is weak and unsuitable for a public deployment).

Seed the hashes with setup_auth.py after migrating.
"""
from werkzeug.security import check_password_hash, generate_password_hash

from db import one


def verify(user_id: str, password: str):
    u = one(
        "SELECT TRIM(user_id) AS user_id, COALESCE(user_name,'') AS user_name, "
        "RTRIM(COALESCE(class,'')) AS cls, disabled, password_hash "
        "FROM users WHERE UPPER(TRIM(user_id)) = ?",
        user_id.strip().upper(),
    )
    if not u or not u.get("password_hash"):
        return None
    if check_password_hash(u["password_hash"], password):
        return u
    return None


def hash_password(password: str) -> str:
    return generate_password_hash(password)
