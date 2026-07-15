"""Add and seed the password_hash column on `users` (run once after migrating).

Every active user gets the same initial password so you can sign in immediately;
change it later. Set the password via the SEED_PASSWORD env var (default below).

  python setup_auth.py                 # seed all active users with SEED_PASSWORD
  SEED_PASSWORD=... python setup_auth.py
"""
import os
from db import get_conn
from auth import hash_password

SEED = os.environ.get("SEED_PASSWORD", "HrisL98!2026")


def main():
    with get_conn() as c:
        with c.cursor() as cur:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash text;")
            cur.execute("SELECT TRIM(user_id) AS uid FROM users ORDER BY user_id")
            uids = [r["uid"] for r in cur.fetchall()]
            for uid in uids:
                cur.execute("UPDATE users SET password_hash=%s WHERE TRIM(user_id)=%s",
                            (hash_password(SEED), uid))
        c.commit()
    print(f"Seeded {len(uids)} active users with the initial password.")
    print(f"Sign in with any of: {', '.join(uids[:8])}{' …' if len(uids) > 8 else ''}")
    print(f"Initial password: {SEED}   (set SEED_PASSWORD to change; rotate after first login)")


if __name__ == "__main__":
    main()
