"""
app.py
------
Entry point. If the user is already logged in, send them straight to the
Dashboard. Otherwise show Login / Register tabs.

Streamlit's multipage apps auto-build a sidebar nav from everything in
pages/, but we only want logged-in users to see/use those pages, so each
page starts with auth.require_login() (see core/auth.py).
"""

import streamlit as st

from core.db import init_db
from core import auth

st.set_page_config(page_title="PodCraft AI — Podcast Script Generator", page_icon="🎙️", layout="wide")

init_db()  # safe to call every run; only creates tables if missing

if auth.current_user():
    st.switch_page("pages/1_Dashboard.py")

st.markdown(
    "<h1 style='text-align:center;'>🎙️ PodCraft AI</h1>"
    "<p style='text-align:center;color:gray;'>Generate professional podcast scripts with AI</p>",
    unsafe_allow_html=True,
)

_, center, _ = st.columns([1, 1.2, 1])

with center:
    tab_login, tab_register = st.tabs(["Log In", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", use_container_width=True)

        if submitted:
            success, message = auth.login(email, password)
            if success:
                st.success(message)
                st.switch_page("pages/1_Dashboard.py")
            else:
                st.error(message)

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Full Name")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password")
            reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

        if reg_submitted:
            success, message = auth.register(name, reg_email, reg_password, confirm_password)
            if success:
                st.success(message + " Switch to the Log In tab.")
            else:
                st.error(message)

st.markdown(
    "<p style='text-align:center;color:gray;font-size:0.85em;margin-top:2em;'>"
    "New accounts start with 5 free script credits.</p>",
    unsafe_allow_html=True,
)
