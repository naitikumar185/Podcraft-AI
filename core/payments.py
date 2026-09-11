"""
core/payments.py
-----------------
Razorpay TEST MODE integration.

Flow:
1. create_order() asks Razorpay to create an "order" (just a record that
   says "this much money, for this purpose" — no money moves yet).
2. The Pricing page renders Razorpay's hosted Checkout widget in the
   browser using that order_id.
3. The user pays with Razorpay's official TEST card numbers (fake money,
   nothing is ever charged — see the .env.example / README for the test
   card details).
4. Razorpay's widget returns payment_id, order_id, and a signature to the
   page.
5. verify_signature() re-computes that signature on OUR server using our
   secret key and checks it matches. This is the step that matters for
   security: the frontend can claim anything, but only our server-side
   secret key can produce a signature that matches, so a tampered/fake
   "success" from the browser will fail verification and the plan will
   NOT be upgraded.

No API key or secret is hard-coded anywhere in this file — both come
from environment variables (see .env.example).
"""

import os
import hmac
import hashlib
import razorpay

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")

PLANS = {
    "premium": {"label": "Premium", "amount_inr": 499, "credits": 100},
}


def is_configured():
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


def get_client():
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def create_order(amount_inr: int, receipt: str):
    """Creates a Razorpay order (test mode) for amount_inr rupees.
    Razorpay works in paise, so we multiply by 100."""
    client = get_client()
    order = client.order.create({
        "amount": amount_inr * 100,
        "currency": "INR",
        "receipt": receipt,
        "payment_capture": 1,
    })
    return order  # dict containing "id", "amount", "currency", etc.


def verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Recomputes the HMAC-SHA256 signature server-side and compares it
    to the one the frontend received from Razorpay. This is the official
    verification method Razorpay documents for Checkout (non-webhook)
    integrations."""
    generated_signature = hmac.new(
        key=RAZORPAY_KEY_SECRET.encode("utf-8"),
        msg=f"{order_id}|{payment_id}".encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(generated_signature, signature)
