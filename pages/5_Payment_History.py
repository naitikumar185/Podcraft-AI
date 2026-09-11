import streamlit as st
from core import auth, models

st.set_page_config(page_title="Payment History", page_icon="💳", layout="wide")
auth.require_login()
user = auth.current_user()

st.title("💳 Payment History")

transactions = models.get_transactions_for_user(user["id"])

if not transactions:
    st.info("No transactions yet.")
    st.stop()

STATUS_ICON = {"successful": "✅", "failed": "❌", "pending": "⏳"}

for t in transactions:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
        c1.markdown(f"**{t['plan'].capitalize()} Plan**")
        c2.markdown(f"₹{t['amount']:.0f}")
        c3.markdown(f"{STATUS_ICON.get(t['status'], '')} {t['status'].capitalize()}")
        c4.markdown(f"<span style='color:gray;font-size:0.85em;'>{t['created_at'][:16]}<br>Order: {t['razorpay_order_id']}</span>", unsafe_allow_html=True)
