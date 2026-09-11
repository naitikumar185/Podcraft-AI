"""
make_admin.py
-------------
One-off CLI helper to promote an existing user to the 'admin' role.
Run this from the terminal after that user has registered normally:

    python make_admin.py user@example.com

There is deliberately no way to become an admin through the app's UI —
that's a security decision (role escalation should never be a
self-service checkbox on a public registration form), and it's a good
point to raise in your viva if asked about authorization design.
"""

import sys
from core.db import get_conn, init_db


def make_admin(email: str):
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (email.strip().lower(),))
    row = cur.fetchone()
    if not row:
        print(f"No user found with email: {email}")
        conn.close()
        return
    cur.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email.strip().lower(),))
    conn.commit()
    conn.close()
    print(f"{email} is now an admin.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <email>")
        sys.exit(1)
    make_admin(sys.argv[1])
