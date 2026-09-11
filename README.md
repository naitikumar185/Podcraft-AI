# PodCraft AI — Podcast Script Generator

A full-stack AI SaaS-style application for generating podcast scripts, built on
Streamlit + SQLite + LangChain (Google Gemini) + Razorpay (test mode).

## Features

- Email/password registration & login (bcrypt-hashed passwords)
- Per-user dashboard (credits, plan, recent scripts, stats)
- AI podcast script generation (Gemini via LangChain)
- Script history: search, filter by category, sort, open, edit, copy, download, delete
- Credit system (5 free credits, 100 on premium)
- Razorpay test-mode checkout with backend signature verification
- Payment/transaction history
- Role-based admin panel (users, scripts, revenue, transactions)

## 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

- `GOOGLE_API_KEY` — free key from https://aistudio.google.com/apikey (you can
  also just paste it into the sidebar at runtime instead)
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` — free **Test Mode** keys from
  https://dashboard.razorpay.com (Settings → API Keys → Generate Test Key).
  No business verification is required for test keys.

## 3. Run the app

```bash
streamlit run app.py
```

This opens the app at `http://localhost:8501`. The SQLite database
(`podcast.db`) is created automatically on first run in the project folder.

## 4. Create an account, then make yourself an admin

Register a normal account through the app first, then from the terminal:

```bash
python make_admin.py your_email@example.com
```

Log out and back in — the **Admin** page will now appear in the sidebar.

## 5. Testing payments (Razorpay Test Mode)

On the Pricing page, click **Upgrade to Premium**, then in the Razorpay
checkout popup use one of Razorpay's official test cards:

- Card number: `4111 1111 1111 1111`
- Expiry: any future date (e.g. `12/30`)
- CVV: any 3 digits
- OTP (if asked): `1234`

No real money moves — this is Razorpay's documented test-mode card, and the
payment is verified server-side via HMAC-SHA256 signature check in
`core/payments.py` before any credits/plan are updated.

## Project structure

```
podcast-generator/
├── app.py                    # Login/Register gate (entry point)
├── make_admin.py             # CLI: promote a user to admin
├── requirements.txt
├── .env.example
├── core/
│   ├── db.py                 # SQLite schema + connection
│   ├── auth.py                # register/login/session/password hashing
│   ├── models.py              # scripts/transactions/users CRUD (user-scoped)
│   ├── generator.py           # LangChain + Gemini script generation
│   └── payments.py            # Razorpay order creation + signature verification
└── pages/
    ├── 1_Dashboard.py
    ├── 2_Generate_Script.py
    ├── 3_Script_History.py
    ├── 4_Pricing.py
    ├── 5_Payment_History.py
    ├── 6_Profile.py
    └── 7_Admin.py
```

## What was tested before delivery

Because this build environment has no internet access, the Streamlit/bcrypt/
razorpay packages could not be installed here, so the UI itself could not be
click-tested end-to-end in this sandbox. What *was* verified directly, with
real SQLite reads/writes:

- Database schema creation
- Per-user data isolation — a second user cannot read, edit, or delete a
  script that isn't theirs (the exact requirement your guide flagged)
- Credit deduction logic
- Search/filter/sort queries
- Admin aggregate queries (user counts, revenue, etc.)
- The Razorpay HMAC-SHA256 signature algorithm (verified independently against
  the documented formula)

You should still run through the full checklist below yourself once you have
the packages installed locally — see **Testing Checklist** in
`PROJECT_DOCUMENTATION.md`.
