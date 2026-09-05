# Rectify AI: Autonomous Revenue Recovery Engine

**Rectify AI** is a highly robust, compliant, and fully autonomous Revenue Recovery Engine engineered by Vijit Vishnoi. Built for enterprise scale, it intelligently optimizes debt collection and cart abandonment workflows through dynamic AI scoring while adhering to strict regulatory frameworks.

---

## 1. Executive Summary & Architecture

At its core, Rectify AI leverages a high-throughput **Go-based backend** paired with a responsive **React dashboard**. The system architecture is built around three central pillars:

* **Real-Time Telemetry:** Bi-directional **WebSocket** connections push granular event metrics directly to the client dashboard, eliminating the need for inefficient UI polling.
* **Immutable Audit Ledger:** Every state transition, action, and expected value calculation is recorded in a tamper-proof, **SHA-256 hash-chained** ledger, ensuring absolute cryptographic accountability for compliance audits.
* **Massive Concurrency:** The engine operates on highly concurrent, channel-driven worker pools. It gracefully handles 1,000x batch processing spikes and distributes computational loads without blocking the main event loop or crashing the client.

---

## 2. The "Brain": Expected Value Engine & Context

Rectify AI abandons static flowcharts in favor of a dynamic, Expected Value (EV) state machine.

* **LLM-Powered Scoring:** Utilizing the **Groq LLM API**, the engine evaluates the precise context of a failure (e.g., mapping `insufficient_funds` vs. `invalid_card` taxonomies) to dynamically calculate a real-time Probability of Recovery (`P(Recover)`).
* **Context-Aware Routing:** The AI natively differentiates between event classes. It applies strict, legality-bound recovery sequences for `payment.failed` webhooks, while seamlessly pivoting to margin-based discount math for `checkout.abandoned` funnels. 

---

## 3. The "Hero" Feature: Autonomous Hinglish Voice Agent

When standard nudges fail, the system autonomously escalates to a personalized Voice Recovery rail.

* **Dynamic Script Generation:** The Groq LLM synthesizes contextual, conversational scripts on the fly, bridging language gaps through optimized **Hinglish** (Hindi-English) dialect phrasing.
* **Raw Audio Streaming (TTS Proxy):** To circumvent restrictive and inconsistent browser-level Web Speech APIs, the backend proxies requests directly to Google Translate TTS. It streams the raw `audio/mpeg` bytes directly back to the React client, guaranteeing seamless, cross-platform playback.

---

## 4. The "Muscle": Legal Compliance Guardrails

No AI action is dispatched without passing through a deterministic, hard-coded policy layer. The Go state machine securely intercepts and evaluates every AI decision against strict regulatory guardrails:

* **RBI Mandates:** Enforces mandatory pre-debit notices and strict 24-hour time-locks before allowing a retry on the same or alternative payment rail.
* **TRAI Quiet Hours:** Unconditionally vetoes all outbound communications (calls, nudges, notices) between 9:00 PM and 9:00 AM.
* **Global Attempt Capping:** Protects against aggressive recovery loops by enforcing a global cap on total recovery attempts.
* **Debt Age Hard-Stops:** Automatically aborts all recovery pipelines for receivables exceeding a strict 21-day age limit.
* **Cold-Start Rulebooks:** Bypasses uncalibrated AI scoring for brand new events, enforcing a deterministic onboarding rulebook until enough historical data is collected.

---

## 5. Pre-Dispatch State Guards: Safety Infrastructure

Rectify AI is built on the philosophy of "do no harm." The safety infrastructure operates at the pre-dispatch layer to protect the end-consumer:

* **Idempotency Locks:** Instantaneously drops duplicate webhooks and overlapping events using unique idempotency keys to prevent race conditions.
* **Settlement Abortion:** Out-of-band payment successes instantly flag a transaction as settled. Any in-flight recovery actions are immediately vetoed, guaranteeing a customer is never double-charged.
* **Promise-to-Pay Intercept:** When a customer actively commits to a timeline via the dashboard, the engine logs the promise and completely freezes the AI workflow for that specific Payment ID, silently sleeping until the promised date lapses.

---

## 6. Enterprise Integration & Deployment

Engineered for production readiness, the repository enforces best-in-class security and deployment standards:

* **Graceful Termination:** Go routines and worker pools trap interrupt signals (SIGINT/SIGTERM), ensuring in-flight LLM calls and pending ledger commits are safely flushed before shutting down.
* **Secure Webhook Verification:** All incoming events are cryptographically verified using HMAC-SHA256 signatures, ensuring payloads are authentically signed by the upstream payment gateway.
* **Environment & Secret Management:** Strict `.env` isolation protects LLM API keys and database credentials, preventing accidental leaks into version control.
* **Rate Limiting:** IP-based and token-bucket rate limiters prevent API abuse on public-facing endpoints (e.g., the TTS proxy).

### Local Setup Instructions

1. **Clone & Install:**
   ```bash
   git clone https://github.com/vijitvishnoi/rectify-ai.git
   cd rectify-ai
   ```
2. **Environment Variables:**
   Copy `.env.example` to `.env` and populate your `GROQ_API_KEY` and `WEBHOOK_SECRET`.
3. **Run the Backend (Go):**
   ```bash
   cd backend
   go run main.go
   ```
4. **Run the Frontend (React/Vite):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
