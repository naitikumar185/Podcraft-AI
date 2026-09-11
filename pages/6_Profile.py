import streamlit as st
from core import auth
from core.db import get_conn

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")
auth.require_login()
user = auth.current_user()

st.title("👤 Profile & Settings")

st.subheader("Account Info")
st.write(f"**Name:** {user['name']}")
st.write(f"**Email:** {user['email']}")
st.write(f"**Plan:** {user['plan'].capitalize()}")
st.write(f"**Credits:** {user['credits']}")

st.divider()
st.subheader("Change Password")

with st.form("change_password_form"):
    current_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_new_password = st.text_input("Confirm New Password", type="password")
    submitted = st.form_submit_button("Update Password")

if submitted:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],))
    row = cur.fetchone()

    if not row or not auth.verify_password(current_password, row["password_hash"]):
        st.error("Current password is incorrect.")
    elif len(new_password) < 6:
        st.error("New password must be at least 6 characters.")
    elif new_password != confirm_new_password:
        st.error("New passwords do not match.")
    else:
        cur.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (auth.hash_password(new_password), user["id"]),
        )
        conn.commit()
        st.success("Password updated successfully.")
    conn.close()

st.divider()
if st.button("🚪 Log Out"):
    auth.logout()
    st.switch_page("app.py")
