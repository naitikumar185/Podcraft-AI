import streamlit as st
from core import auth, models

st.set_page_config(page_title="Admin", page_icon="🛠️", layout="wide")
auth.require_login()
auth.require_admin()

st.title("🛠️ Admin Panel")

stats = models.admin_stats()
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Users", stats["total_users"])
col2.metric("Total Scripts", stats["total_scripts"])
col3.metric("Successful Payments", stats["successful_payments"])
col4.metric("Failed Payments", stats["failed_payments"])
col5.metric("Revenue (₹)", f"{stats['revenue']:.0f}")

st.divider()

tab_users, tab_transactions = st.tabs(["Recent Users", "All Transactions"])

with tab_users:
    users = models.recent_users(limit=20)
    if not users:
        st.info("No users yet.")
    else:
        st.dataframe(
            [dict(u) for u in users],
            use_container_width=True, hide_index=True,
        )

with tab_transactions:
    txs = models.all_transactions(limit=50)
    if not txs:
        st.info("No transactions yet.")
    else:
        st.dataframe(
            [dict(t) for t in txs],
            use_container_width=True, hide_index=True,
        )
