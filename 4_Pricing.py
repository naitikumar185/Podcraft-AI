import streamlit as st
import streamlit.components.v1 as components

from core import auth, models, payments

st.set_page_config(page_title="Pricing", page_icon="⭐", layout="wide")
auth.require_login()
user = auth.current_user()

st.title("⭐ Plans & Pricing")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Free")
    st.markdown("### ₹0 / month")
    st.markdown("- 5 script credits\n- All script formats\n- Download as Markdown")
    if user["plan"] == "free":
        st.success("Your current plan")

with col2:
    st.subheader("Premium")
    st.markdown(f"### ₹{payments.PLANS['premium']['amount_inr']} one-time")
    st.markdown(f"- {payments.PLANS['premium']['credits']} script credits\n- Priority support\n- All script formats")
    if user["plan"] == "premium":
        st.success("Your current plan")
    else:
        upgrade_clicked = st.button("Upgrade to Premium", type="primary", use_container_width=True)

st.divider()

if not payments.is_configured():
    st.warning(
        "Payment gateway isn't configured yet. Add RAZORPAY_KEY_ID and "
        "RAZORPAY_KEY_SECRET to your .env file (Razorpay Test Mode keys — "
        "no business verification needed) to enable checkout."
    )
    st.stop()

if user["plan"] != "premium" and 'upgrade_clicked' in dir() and upgrade_clicked:
    order = payments.create_order(
        amount_inr=payments.PLANS["premium"]["amount_inr"],
        receipt=f"user_{user['id']}_premium",
    )
    models.create_transaction(
        user_id=user["id"], plan="premium",
        amount=payments.PLANS["premium"]["amount_inr"],
        razorpay_order_id=order["id"], status="pending",
    )
    st.session_state["pending_order_id"] = order["id"]

if st.session_state.get("pending_order_id"):
    order_id = st.session_state["pending_order_id"]
    st.info("Complete payment below using Razorpay's TEST mode. Use test card "
            "4111 1111 1111 1111, any future expiry, any CVV — no real money moves.")

    checkout_html = f"""
    <div id="rzp-container"></div>
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <script>
      var options = {{
        "key": "{payments.RAZORPAY_KEY_ID}",
        "amount": "{payments.PLANS['premium']['amount_inr'] * 100}",
        "currency": "INR",
        "name": "PodCraft AI",
        "description": "Premium Plan Upgrade",
        "order_id": "{order_id}",
        "handler": function (response) {{
            document.getElementById("rzp-container").innerHTML =
              "<p><b>Payment ID:</b> " + response.razorpay_payment_id + "</p>" +
              "<p><b>Order ID:</b> " + response.razorpay_order_id + "</p>" +
              "<p><b>Signature:</b> " + response.razorpay_signature + "</p>" +
              "<p>Copy these three values into the confirmation form below in the app.</p>";
        }},
        "theme": {{ "color": "#6C5CE7" }}
      }};
      var rzp = new Razorpay(options);
      rzp.open();
    </script>
    """
    components.html(checkout_html, height=250)

    st.caption("After paying in the widget above, paste the three values it shows you here to confirm:")
    with st.form("verify_payment_form"):
        payment_id = st.text_input("Payment ID")
        signature = st.text_input("Signature")
        verify_submitted = st.form_submit_button("Confirm Payment", type="primary")

    if verify_submitted:
        if payments.verify_signature(order_id, payment_id, signature):
            models.mark_transaction(order_id, status="successful", razorpay_payment_id=payment_id)
            models.upgrade_to_premium(user["id"], credits_granted=payments.PLANS["premium"]["credits"])
            auth.refresh_current_user()
            st.session_state.pop("pending_order_id", None)
            st.success("Payment verified! You're now on the Premium plan.")
            st.balloons()
        else:
            models.mark_transaction(order_id, status="failed", razorpay_payment_id=payment_id)
            st.error("Signature verification failed. This payment could not be confirmed as authentic.")
