# Project Documentation

## Project Title
PodCraft AI — An AI-Powered Podcast Script Generator with User Management and Subscription Billing

## Abstract
Creating a podcast requires writing a structured script — an introduction,
main discussion segments, and a conclusion — which is time-consuming for
independent creators. This project is a web application that uses a large
language model (Google Gemini, via LangChain) to generate a complete podcast
script from a few inputs (topic, audience, tone, duration, etc.). Beyond
generation, the application implements the concerns of a real multi-user
product: account registration and login, per-user script storage and history,
a credit-based usage system, a subscription upgrade path with sandboxed
payment processing (Razorpay Test Mode, verified server-side), and an admin
panel for oversight — built with Streamlit, SQLite, and the Razorpay Python
SDK.

## Problem Statement
Existing simple AI script generators are single-use, stateless tools: a user
generates text and it disappears when the page is refreshed. There is no
concept of an account, no history of previously generated work, no way to
track usage, and no monetization path. This project addresses that gap by
turning a one-off generation script into a persistent, multi-user application
with authentication, storage, and billing.

## Objectives
1. Allow users to securely register and log in.
2. Let each user generate podcast scripts using AI and have them saved
   automatically to their own account.
3. Let users search, filter, edit, copy, download, and delete their past
   scripts, with strict access control so one user can never see another
   user's data.
4. Implement a credit-based usage limit with a paid upgrade path.
5. Integrate a real payment gateway in sandbox/test mode with backend
   signature verification (not just a frontend "success" message).
6. Provide an admin view of platform-wide statistics.

## Existing System
The starting point was a single-file Streamlit script with no persistence,
no accounts, and no database — a user pasted their own Gemini API key,
filled a form, and received a script that existed only until the page was
refreshed.

## Proposed System
A multipage Streamlit application backed by a SQLite database, with:
- An authentication layer (bcrypt password hashing, session-based login)
- A relational schema for users, scripts, and transactions
- Credit tracking enforced on the backend, not just hidden in the UI
- Razorpay Test Mode checkout with HMAC-SHA256 signature verification
  performed on the server before any plan/credit change is applied
- Role-based access control separating regular users from admins

## Features
See `README.md` for the full feature list.

## Technology Stack
| Layer | Technology | Reason |
|---|---|---|
| UI + application logic | Streamlit (multipage) | Rapid development, Python-only, good for a single-developer academic project |
| Database | SQLite | Zero-configuration, single-file, easy to inspect during a viva |
| AI | Google Gemini via LangChain (LCEL) | Reused from the original project; free-tier API key |
| Auth | bcrypt + Streamlit session state | Industry-standard adaptive password hashing |
| Payments | Razorpay Python SDK (Test Mode) | Free test keys with no business verification; standard for Indian student projects |

## System Architecture
The application follows a simple layered architecture:
- **Presentation layer**: `app.py` + `pages/*.py` (Streamlit pages)
- **Business logic layer**: `core/auth.py`, `core/generator.py`, `core/payments.py`
- **Data access layer**: `core/models.py` (all SQL lives here)
- **Data layer**: `core/db.py` + `podcast.db` (SQLite file)

Every page in `pages/` calls `auth.require_login()` (and `auth.require_admin()`
for the admin page) before rendering anything, which is the application's
route-protection mechanism.

## Modules
1. Authentication Module (`core/auth.py`)
2. Script Generation Module (`core/generator.py`, `pages/2_Generate_Script.py`)
3. Script History Module (`core/models.py` scripts functions, `pages/3_Script_History.py`)
4. Credit & Subscription Module (`core/models.py` credit functions, `pages/4_Pricing.py`)
5. Payment Module (`core/payments.py`, `pages/4_Pricing.py`, `pages/5_Payment_History.py`)
6. Admin Module (`pages/7_Admin.py`)

## Database Design

**users** — id, name, email (unique), password_hash, role, plan, credits, created_at
**scripts** — id, user_id (FK), title, topic, content, category, duration, num_speakers, speaker_names, language, tone, created_at, updated_at
**transactions** — id, user_id (FK), plan, amount, razorpay_order_id, razorpay_payment_id, status, created_at

## ER Diagram Explanation
There are two one-to-many relationships, both rooted at `users`:
- One user → many scripts (`scripts.user_id` references `users.id`)
- One user → many transactions (`transactions.user_id` references `users.id`)

Both foreign keys are indexed, since every history/payment lookup filters by
`user_id`. There is no many-to-many relationship in this schema — it was kept
intentionally simple.

## Data Flow
1. User submits the generation form → validated in the UI.
2. `core/generator.py` builds a prompt and calls the Gemini API through
   LangChain.
3. On success, the returned script text is written to the `scripts` table via
   `core/models.py`, tagged with the logged-in user's `id`.
4. One credit is deducted from that user's row — only after the AI call
   succeeds.
5. The Dashboard and Script History pages read directly from the database,
   always filtered by the current session's `user_id`.

## Authentication Flow
1. Register: input validated → password hashed with bcrypt → row inserted
   into `users` with `role='user'`, `plan='free'`, `credits=5`.
2. Login: email looked up → `bcrypt.checkpw` compares the submitted password
   against the stored hash → on success, a trimmed copy of the user row
   (no password hash) is placed in `st.session_state["user"]`.
3. Every protected page checks `st.session_state["user"]` at the top and
   redirects to the login page if absent.
4. Logout clears that session key.

## Payment Flow
1. User clicks "Upgrade to Premium" → backend creates a Razorpay *order*
   (amount + currency, no money moved yet) and stores a `pending`
   transaction row.
2. Razorpay's hosted Checkout widget (loaded via `checkout.razorpay.com`)
   collects card details directly — the application never sees or stores
   raw card numbers.
3. On completion, Razorpay's widget returns `payment_id`, `order_id`, and a
   `signature` to the browser.
4. The app recomputes the expected signature server-side using
   `HMAC-SHA256(order_id + "|" + payment_id, key_secret)` and compares it to
   the one returned. Only a matching signature — which requires knowledge of
   the secret key, held only on the server — is accepted.
5. On a verified match: transaction marked `successful`, user's `plan` and
   `credits` updated. On mismatch: transaction marked `failed`, nothing else
   changes.

## User Roles
- **user** (default): can manage their own scripts, credits, and payments.
- **admin**: additionally sees platform-wide stats, all users, and all
  transactions. There is no UI path to grant yourself admin — it's done via
  the `make_admin.py` CLI script, by design (see README).

## Security Features
- Passwords hashed with bcrypt (never stored or compared as plain text)
- Every script/transaction database query is scoped by `user_id` from the
  session — never from a URL parameter or client-supplied value
- Payment success is verified via a cryptographic signature check on the
  server, not trusted from the frontend
- Secrets (Gemini key, Razorpay key/secret) are read from environment
  variables, never hard-coded
- `.env` and the SQLite database file are excluded from version control via
  `.gitignore`
- Role-based access control gates the admin page

## Future Scope
- Export scripts as audio using a text-to-speech API
- Team/organization accounts with shared script libraries
- Recurring (monthly) subscriptions instead of one-time premium unlock
- Email verification and password-reset-via-email flow

## Conclusion
This project extends a minimal, stateless AI script generator into a
multi-user application that demonstrates authentication, authorization,
relational data modeling, CRUD operations, third-party API integration (both
AI and payments), and secure handling of secrets and payment verification —
while staying small enough (roughly a dozen files) to fully explain in a
viva.

---

## Testing Checklist

Run these manually once the app is running locally (`streamlit run app.py`):

- [ ] Register a new account
- [ ] Try registering the same email again → should be rejected
- [ ] Log in with correct credentials
- [ ] Log in with a wrong password → should show an error, not log in
- [ ] Visit `pages/1_Dashboard.py` directly while logged out → should redirect to login
- [ ] Generate a script with a valid Gemini API key → should save to history and deduct 1 credit
- [ ] Generate a script with an invalid/missing API key → should show an error and NOT deduct a credit
- [ ] Open Script History → confirm the new script appears
- [ ] Search/filter/sort in Script History
- [ ] Edit a script and save → confirm the change persists after reopening
- [ ] Copy a script (via the code-block copy icon) and download it
- [ ] Delete a script → confirm it's gone
- [ ] Register a second account, log in as it, and confirm you cannot see the first account's scripts under any circumstance
- [ ] Use up all 5 free credits → confirm the Generate page blocks further generation and points to Pricing
- [ ] Go to Pricing, upgrade using Razorpay's test card → confirm the transaction shows "successful" and credits/plan update
- [ ] Attempt to submit a fake/garbled signature → confirm it's rejected and marked "failed"
- [ ] View Payment History → confirm the transaction appears with correct status
- [ ] Run `make_admin.py` on one account, log in as it → confirm the Admin page appears and shows correct stats
- [ ] Log in as a non-admin and try to open `pages/7_Admin.py` directly → should be blocked
- [ ] Resize the browser window / open on mobile width → confirm layout stays usable

## Viva Questions & Answers

**Q: Why SQLite instead of MySQL/PostgreSQL?**
A: SQLite needs no separate server process — the entire database is one file,
which is simpler to set up, run, and demonstrate for a project of this scope.
The schema uses standard SQL and foreign keys, so it would port to
PostgreSQL/MySQL with minimal changes if the project needed to scale.

**Q: How do you stop User A from viewing User B's scripts by changing an ID?**
A: Every script/transaction query in `core/models.py` requires the requesting
user's `id` as a parameter and includes it in the `WHERE` clause
(`WHERE id = ? AND user_id = ?`). That `user_id` always comes from the
server-side session (`st.session_state`), which the client cannot edit — so
even if someone tried to reference another script's ID, the query would
simply return nothing because the `user_id` wouldn't match.

**Q: Why bcrypt instead of storing SHA-256 hashes?**
A: bcrypt is a deliberately slow, adaptive hashing algorithm designed for
passwords — it includes a per-password random salt automatically and can be
tuned to stay slow as hardware improves, which makes brute-force and
rainbow-table attacks impractical. Plain SHA-256 is fast, which is exactly
the wrong property for password storage.

**Q: How do you know a payment actually succeeded, instead of trusting the browser?**
A: Razorpay signs each successful payment with an HMAC-SHA256 signature
generated using the merchant's secret key, which never leaves the server.
The app recomputes that same signature server-side from the order ID and
payment ID and compares it to what the browser reported. Only Razorpay
(which holds the same secret) could have produced a signature that matches,
so a client trying to fake a "success" message would fail this check.

**Q: What happens if the AI call fails halfway through generation?**
A: The script is only saved to the database, and the credit only deducted,
inside the `else` branch that runs after a successful return from
`generate_script()`. Any exception is caught, shown to the user as an error,
and neither the save nor the credit deduction happens — so a failed
generation never costs the user a credit.

**Q: Why is there no "sign up as admin" option?**
A: Letting anyone self-assign an admin role during registration would be a
serious authorization flaw — it defeats the purpose of having roles at all.
Admin promotion is instead a one-off action performed outside the web app
(`make_admin.py`), simulating how a real system administrator would grant
elevated access.

**Q: What would you change if this had to support many more users?**
A: Move from SQLite to PostgreSQL for better concurrent write handling, move
session state out of Streamlit's in-memory session into a proper token-based
auth system (e.g. JWT) if migrating off Streamlit, and switch Razorpay's
one-time "premium unlock" into a real recurring subscription using Razorpay
Subscriptions with webhook-based renewal handling instead of a single
Checkout payment.
