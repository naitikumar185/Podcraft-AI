import streamlit as st
from core import auth, models

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")
auth.require_login()
user = auth.current_user()

st.title(f"Welcome back, {user['name']} 👋")

total_scripts, this_month = models.count_scripts_for_user(user["id"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Scripts", total_scripts)
col2.metric("Scripts This Month", this_month)
col3.metric("Credits Remaining", user["credits"])
col4.metric("Current Plan", user["plan"].capitalize())

st.divider()

left, right = st.columns([1, 2])
with left:
    st.subheader("Quick Actions")
    if st.button("✍️ Generate New Script", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Generate_Script.py")
    if st.button("📚 View Script History", use_container_width=True):
        st.switch_page("pages/3_Script_History.py")
    if user["plan"] == "free":
        if st.button("⭐ Upgrade to Premium", use_container_width=True):
            st.switch_page("pages/4_Pricing.py")

with right:
    st.subheader("Recent Scripts")
    recent = models.get_scripts_for_user(user["id"])[:5]
    if not recent:
        st.info("You haven't generated any scripts yet. Click 'Generate New Script' to get started.")
    else:
        for s in recent:
            with st.container(border=True):
                st.markdown(f"**{s['title'] or 'Untitled'}**  \n"
                             f"<span style='color:gray;font-size:0.85em;'>{s['topic']} · {s['created_at'][:16]}</span>",
                             unsafe_allow_html=True)
