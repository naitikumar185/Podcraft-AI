"""
core/models.py
--------------
All database reads/writes for scripts, transactions, and user
credits/plan live here, in one place, so it's easy to audit that every
script/transaction query is scoped by user_id.

IMPORTANT SECURITY NOTE (this is the answer to "how do you stop User A
from reading User B's scripts"): every function below that touches the
`scripts` or `transactions` table takes the current user's id as an
argument and includes `WHERE user_id = ?` in the SQL. The id always comes
from st.session_state["user"]["id"] (set at login), never from a page
URL or a value the user can edit, so there is no id a user could type in
to fetch someone else's row.
"""

from datetime import datetime
from core.db import get_conn


# ---------- Scripts ----------

def create_script(user_id: int, title, topic, content, category, duration,
                   num_speakers, speaker_names, language, tone):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("""
        INSERT INTO scripts
            (user_id, title, topic, content, category, duration,
             num_speakers, speaker_names, language, tone, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, title, topic, content, category, duration,
          num_speakers, speaker_names, language, tone, now, now))
    conn.commit()
    script_id = cur.lastrowid
    conn.close()
    return script_id


def get_scripts_for_user(user_id: int, search: str = "", category: str = "All", sort: str = "newest"):
    conn = get_conn()
    cur = conn.cursor()

    query = "SELECT * FROM scripts WHERE user_id = ?"
    params = [user_id]

    if search:
        query += " AND (title LIKE ? OR topic LIKE ?)"
        like = f"%{search}%"
        params += [like, like]

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY created_at " + ("ASC" if sort == "oldest" else "DESC")

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_script(script_id: int, user_id: int):
    """Fetches one script, but ONLY if it belongs to user_id. Returns None otherwise."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scripts WHERE id = ? AND user_id = ?", (script_id, user_id))
    row = cur.fetchone()
    conn.close()
    return row


def update_script(script_id: int, user_id: int, title, content):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE scripts SET title = ?, content = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (title, content, datetime.utcnow().isoformat(), script_id, user_id))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def delete_script(script_id: int, user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM scripts WHERE id = ? AND user_id = ?", (script_id, user_id))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def count_scripts_for_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM scripts WHERE user_id = ?", (user_id,))
    total = cur.fetchone()["c"]
    cur.execute("""
        SELECT COUNT(*) as c FROM scripts
        WHERE user_id = ? AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
    """, (user_id,))
    this_month = cur.fetchone()["c"]
    conn.close()
    return total, this_month


# ---------- Credits / plan ----------

def deduct_credit(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET credits = credits - 1 WHERE id = ? AND credits > 0", (user_id,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def upgrade_to_premium(user_id: int, credits_granted: int = 100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET plan = 'premium', credits = credits + ? WHERE id = ?",
        (credits_granted, user_id),
    )
    conn.commit()
    conn.close()


# ---------- Transactions ----------

def create_transaction(user_id: int, plan: str, amount: float, razorpay_order_id: str, status: str = "pending"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (user_id, plan, amount, razorpay_order_id, status)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, plan, amount, razorpay_order_id, status))
    conn.commit()
    tx_id = cur.lastrowid
    conn.close()
    return tx_id


def mark_transaction(razorpay_order_id: str, status: str, razorpay_payment_id: str = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE transactions SET status = ?, razorpay_payment_id = ?
        WHERE razorpay_order_id = ?
    """, (status, razorpay_payment_id, razorpay_order_id))
    conn.commit()
    conn.close()


def get_transactions_for_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------- Admin-only aggregate queries ----------

def admin_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM users")
    total_users = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM scripts")
    total_scripts = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM transactions WHERE status = 'successful'")
    successful_payments = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM transactions WHERE status = 'failed'")
    failed_payments = cur.fetchone()["c"]
    cur.execute("SELECT COALESCE(SUM(amount), 0) as s FROM transactions WHERE status = 'successful'")
    revenue = cur.fetchone()["s"]
    conn.close()
    return {
        "total_users": total_users,
        "total_scripts": total_scripts,
        "successful_payments": successful_payments,
        "failed_payments": failed_payments,
        "revenue": revenue,
    }


def recent_users(limit: int = 10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, plan, role, created_at FROM users ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def all_transactions(limit: int = 50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.*, u.name as user_name, u.email as user_email
        FROM transactions t JOIN users u ON t.user_id = u.id
        ORDER BY t.created_at DESC LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
