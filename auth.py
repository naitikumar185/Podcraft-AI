"""
core/auth.py
------------
Registration, login, logout, and session handling.

Passwords: hashed with bcrypt (salted automatically per-password). We never
store or compare plain-text passwords anywhere in the app.

Session: Streamlit's st.session_state persists for the lifetime of a
browser tab, so once a user logs in we store their user row (minus the
password hash) in st.session_state["user"]. Every protected page checks
for this before rendering anything.
"""

import re
import bcrypt
import streamlit as st

from core.db import get_conn

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def register(name: str, email: str, password: str, confirm_password: str):
    """Returns (success: bool, message: str)."""
    name = name.strip()
    email = email.strip().lower()

    if not name or not email or not password:
        return False, "All fields are required."
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if password != confirm_password:
        return False, "Passwords do not match."

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cur.fetchone():
        conn.close()
        return False, "An account with this email already exists."

    cur.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, hash_password(password)),
    )
    conn.commit()
    conn.close()
    return True, "Account created successfully. Please log in."


def login(email: str, password: str):
    """Returns (success: bool, message: str). On success also sets st.session_state['user']."""
    email = email.strip().lower()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return False, "No account found with that email."
    if not verify_password(password, row["password_hash"]):
        return False, "Incorrect password."

    st.session_state["user"] = {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "plan": row["plan"],
        "credits": row["credits"],
    }
    return True, "Logged in successfully."


def logout():
    st.session_state.pop("user", None)


def current_user():
    """Returns the logged-in user dict, or None."""
    return st.session_state.get("user")


def refresh_current_user():
    """Re-reads the logged-in user's row from the DB (call after credits/plan change)."""
    user = current_user()
    if not user:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user["id"],))
    row = cur.fetchone()
    conn.close()
    if row:
        st.session_state["user"] = {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "role": row["role"],
            "plan": row["plan"],
            "credits": row["credits"],
        }


def require_login():
    """Call at the top of every protected page. Redirects to the login gate if not logged in."""
    if not current_user():
        st.warning("Please log in to view this page.")
        st.switch_page("app.py")
        st.stop()


def require_admin():
    """Call at the top of admin-only pages. Assumes require_login() already ran."""
    user = current_user()
    if not user or user["role"] != "admin":
        st.error("You don't have permission to view this page.")
        st.stop()
