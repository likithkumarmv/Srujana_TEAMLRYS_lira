# LIRA v6.0 --- Android Customer App Upgrade PRD

**Project:** LIRA --- Live Interruption & Ring Analysis\
**Track:** F-01 Financial Fraud and Transaction Risk Detection\
**Target:** Upgrade the existing Android application only\
**Audience:** Developer using Antigravity IDE\
**Status:** Implementation specification

------------------------------------------------------------------------

## 1. Objective

Upgrade the existing LIRA Android app into the customer-facing mobile
client for LIRA v6.0. The app must connect to the **same FastAPI backend
and Supabase-backed canonical state** that will be used by the web
console and ESP32 terminal.

This PRD covers **Android only**. Do not build the website or ESP32
firmware as part of this task. Do not modify backend/database contracts
unless the developer identifies a specific missing contract and
documents it separately.

### Core principle

The Android app is a client, not the authority. It submits requests to
FastAPI and displays backend-confirmed responses. It must never
independently calculate the authoritative payment outcome, release a
held payment, or claim a cancellation succeeded before the backend
confirms it.

### Existing-code preservation rule

Before editing: 1. Inspect the complete existing Android project. 2.
Identify package/application ID, Kotlin and Gradle versions,
architecture, navigation, theme, screens, dependencies, API clients,
Supabase usage, and build/run instructions. 3. Identify existing
functionality and preserve working UI/components where practical. 4.
Create a clear implementation plan and list files to change before major
refactoring. 5. Do not replace the project with a fresh template, rename
package IDs, upgrade unrelated dependencies, or remove existing features
without a documented reason. 6. Build the app before and after changes.
Fix regressions introduced by this task.

If source code is not available, do not pretend to have inspected it.
Request the existing Android project or work only with the files
available.

------------------------------------------------------------------------

## 2. Product context

LIRA analyses simulated financial transactions to identify and
prioritize potentially suspicious activity. It considers sender
behaviour, transaction history, receiver indicators and related
transaction patterns. For this prototype, the Android app is the
customer-side interface for initiating a simulated payment, viewing the
outcome and responding to a safety intervention.

The app must clearly state that: - payments are synthetic and
simulated; - no real funds are transferred, frozen, recovered or
returned; - the prototype is not connected to a bank, UPI, NPCI or
production payment rail; - call mode is either simulated or a live
test-provider call to a consenting participant.

The app supports the F-01 goal by making risk decisions understandable
to the customer without exposing unnecessary internal scoring details
that make the system easy to game.

------------------------------------------------------------------------

## 3. Required technology and integration

-   Preserve the existing Android technology stack where practical.
-   Target Kotlin + Jetpack Compose if the existing project already uses
    it; do not force a rewrite if it uses another functioning Android
    architecture.
-   Use a single API/repository layer for network access.
-   FastAPI is the authority for scoring, priority, payment state, hold
    expiry, call state, trusted-person eligibility and cancellation.
-   Supabase Postgres is the canonical persistent state, accessed
    through the backend for business operations.
-   Do not use direct client-side Supabase writes for payments, case
    transitions, officer approvals, trusted-person outcomes or audit
    events.
-   Do not embed Supabase service-role keys, database credentials,
    voice-provider secrets or admin credentials in the APK.
-   API base URL must be configurable by build variant/environment, not
    hard-coded across screens.
-   `localhost` on the developer laptop is not the Android device's
    localhost. Support a configurable LAN URL for local testing and
    HTTPS URL for hosted demo.
-   Use HTTPS for deployed builds. Do not disable TLS verification as a
    workaround.

### Required app layers

``` text
Compose UI / existing UI framework
          |
ViewModel / presentation state
          |
Repository / domain mapping
          |
Typed API client (Retrofit/OkHttp or existing client)
          |
FastAPI /api/v1
          |
Supabase Postgres (canonical state)
```

Keep responsibilities separate. UI components must not call database
APIs or implement payment policy.

------------------------------------------------------------------------

## 4. Functional scope and screens

Retain current screen structure where it is useful, but ensure the
following user journeys are supported.

### 4.1 Home / Payment entry

Purpose: let a demo customer initiate a simulated payment.

Requirements: - Prominent persistent label: **SIMULATED PAYMENT --- NO
REAL MONEY MOVES**. - Recipient selection or pseudonymous recipient
identifier based on existing backend data. - Amount input in INR;
validate positive value and supported maximum. - Optional memo field if
compatible with current model. - Clear submit/loading state and
protection against repeated taps. - Generate an idempotency key for a
new payment attempt and reuse it if the request is retried. - Submit to
`POST /api/v1/payments`. - Do not calculate the final risk score or
outcome on the device. - Display the payment ID and server-returned
state after success. - Show accessible validation and network errors. -
Recent payment list loads from the backend, not only in-memory state.

### 4.2 Payment result

Purpose: explain what the backend decided.

Display: - Amount and recipient pseudonym. - Payment/case reference. -
Backend-confirmed state: `LAG_HOLD`, `SUSPICION_HOLD`, `EXECUTED`, or
`STOPPED`. - Priority (`P1`, `P2`, `P3`, `PASS`) and risk summary where
permitted. - Short customer-safe explanation of why the payment was
flagged. - What happens next and which actions are currently
available. - `SIMULATED` label.

Do not label a customer or receiver a criminal or confirmed fraudster.
Explain observed signals without exposing sensitive details
unnecessarily. For example, use "This payment differs from your recent
activity" rather than a raw internal rule code alone.

### 4.3 Payment detail / hold screen

Support both hold types: - `LAG_HOLD` - `SUSPICION_HOLD`

Show: - Current server-confirmed state and version/last-updated time. -
Hold start and expiry if returned by the API. - Clear next step. -
Cancellation button only when the server says the case is cancellable;
the backend still validates it. - A pending-cancellation status distinct
from `STOPPED`. - If a stale client version causes a conflict, fetch the
latest payment/case and show the updated state. - If a hold expires,
display the server-confirmed result and its reason.

Never use only a local countdown to change a payment state. A countdown
is informational; backend state is authoritative.

### 4.4 Cancel flow and offline behavior

This behavior is mandatory.

When online: 1. Customer taps Cancel. 2. App submits
`POST /api/v1/cases/{id}/cancel` with an idempotency key and expected
version. 3. App shows the confirmed server result. 4. If the case is
already `EXECUTED` or `STOPPED`, show the returned end state and explain
that the cancellation request arrived too late.

When offline: - Show the last confirmed state with a clear `STALE`
banner. - On Cancel, display exactly: **CANCEL REQUESTED --- NOT YET
CONFIRMED**. - Persist the cancellation request safely and retry with
the **same idempotency key** after connectivity returns. - Do not change
the payment to `STOPPED` locally. - On reconnect, fetch current server
state before retrying the cancellation request. - If the server says
expiry already changed the case to `STOPPED`, explain it was stopped by
the hold-expiry rule, not by the customer's cancel request. - If the
server says it was already `EXECUTED`, show that state and explain
cancellation could not reverse it. - Never queue or replay an officer
release from Android. - If a cancellation response is ambiguous due to
timeout, retain the pending state and retry idempotently.

Use Android's persistent work scheduling mechanism if available in the
current app (e.g. WorkManager) for retry. Do not create an aggressive
battery-draining polling loop.

### 4.5 Safety check / AI call status

Display call events returned by backend: - Call type: customer
interruption or trusted-person call, if relevant. - Call mode label
sourced from the server record: - **SIMULATED CALL** ---
text-to-speech/simulated twin, no phone network. - **LIVE CALL (test
provider)** --- real test-provider call to consenting participants. -
Call status and timestamps. - Short safe summary of outcome and next
steps.

Rules: - The client must not infer call mode from local settings or a
provider name. - The backend `mode` field determines the displayed
label. - Never ask for or display requests for OTP, PIN, password, CVV
or full credentials. - A call result alone must never show that a held
payment was released. - If no call is configured, show a clear "No call
initiated" state rather than fabricating one. - The app does not
directly call arbitrary phone numbers. It requests the configured
backend workflow.

### 4.6 Trusted-person settings/status

Implement only what the existing backend contract supports. Display: -
Whether trusted-person protection is required for a current payment. -
Enrolment/consent status and cooling-period message where applicable. -
Opt-in/opt-out controls only if authorized backend endpoints exist. -
The effect of a pending change, including the 24-hour cooling period if
configured.

Policy: - `needs_trusted = covered_customer AND amount > ₹50,000`. -
Prototype coverage: customer aged 70+ (covered by default, opt-out after
24 hours under prototype policy) or customer opted in. -
Disability-based eligibility is out of scope for this prototype; do not
imply it is supported. - The under-₹10,000 risk-hold exemption is
separate and takes precedence over risk-based holds. - The app must not
calculate `needs_trusted` itself; display the backend result. -
Trusted-person approval is not proof of safety and does not by itself
release a suspicion-held payment.

If the current API lacks trusted-person settings endpoints, implement
read-only status and document the missing contract rather than inventing
endpoints or writing directly to Supabase.

### 4.7 Payment history

Requirements: - Load recent payments from `GET /api/v1/payments` or the
existing agreed list endpoint. - Display amount, recipient, created
time, state, priority and simulation label. - Open detail by payment ID
and refresh authoritative state. - Support pagination or a bounded
recent list. - Persisted server data must remain visible after app
restart/reinstall/login as supported by the existing auth model. - Do
not treat local cache as the canonical history.

### 4.8 Connection and error states

Provide clear states for: - Connected. - Offline. - Backend
unavailable. - Stale cached state. - Request pending. - Request timed
out/unknown result. - Version conflict (`409`). - Authorization
failure. - Invalid request. - Server error.

For `409`, parse current state/version if provided, refetch, and explain
that the case changed. Do not silently retry a non-idempotent action
with a new key.

------------------------------------------------------------------------

## 5. API contract

Use the agreed FastAPI v6.0 contract. Confirm endpoint names against the
actual backend before coding; do not silently create incompatible
endpoints.

Expected endpoints: - `POST /api/v1/payments` --- create a simulated
payment and receive authoritative decision. - `GET /api/v1/payments` ---
list/history. - `GET /api/v1/payments/{id}` --- payment detail and
current state/version. - `GET /api/v1/cases/{id}` --- case data, when a
case exists. - `POST /api/v1/cases/{id}/cancel` --- cancellation
request. - Any agreed read-only trusted-person/call endpoints already
implemented by backend.

### Request conventions

-   State-changing requests use `Idempotency-Key`.
-   Requests to mutate a versioned case include the expected
    case/payment version as agreed with backend.
-   Never send a client-chosen final state like `EXECUTED` or `STOPPED`.
-   Validate and map server errors consistently.
-   Use a request ID for logs where supported.
-   Do not invent response fields; inspect OpenAPI/schema or existing
    backend code.

### Example response concepts

The API response should provide some or all of: - Payment ID, case ID,
amount, recipient reference. - State, version, priority, score/risk band
if safe to show. - Plain-language reasons. - Hold start/expiry and
server time. - `needs_trusted` and trusted-person status. - Call records
with server-owned `mode`. - `simulation=true`.

If actual response schemas differ, adapt the Android DTOs to the backend
contract rather than changing backend semantics just to fit a guessed
DTO.

------------------------------------------------------------------------

## 6. Risk thresholds: customer-facing behavior

The app must display the server's decision, not recreate it. Add UI/unit
tests and integration tests that validate the app correctly renders
results for these boundary cases:

  --------------------------------------------------------------------------
                        Amount Server decision         App requirement
  ---------------------------- ----------------------- ---------------------
                    ₹9,999, P1 `EXECUTED` with review  Do not show a risk
                               flag                    hold; explain that
                                                       additional review may
                                                       occur

                   ₹10,000, P1 `SUSPICION_HOLD`        Show hold and next
                                                       step

     ₹50,000, covered customer `needs_trusted=false`   Do not ask for
                               by amount rule          trusted-person
                                                       approval based solely
                                                       on amount

     ₹50,001, covered customer `needs_trusted=true`    Show trusted-person
                                                       step if returned by
                                                       server
  --------------------------------------------------------------------------

Do not imply these thresholds are universal regulatory requirements.
They are prototype policy settings.

------------------------------------------------------------------------

## 7. UX and visual quality

-   Retain existing brand/theme unless it conflicts with usability or
    simulation clarity.
-   Build a clean, credible financial-security interface; prioritize
    readability over excessive animations.
-   Clearly distinguish normal, held, stopped, and executed simulated
    states with text and icons, not color alone.
-   Make "SIMULATED PAYMENT --- NO REAL MONEY MOVES" visible on payment
    flows and history.
-   Keep error messages actionable and nontechnical; detailed
    diagnostics can go to debug logs.
-   Use accessible touch targets, font sizes, contrast, screen-reader
    labels and keyboard behavior.
-   Avoid exposing raw risk feature weights to the customer. Show
    concise, truthful explanations.
-   Never call a receiver a criminal or a confirmed mule.
-   Use local timezone for presentation and preserve UTC timestamps from
    backend.
-   Keep loading and empty states intentional, not blank screens.
-   Do not add decorative screens unrelated to the defined workflow.

------------------------------------------------------------------------

## 8. Security and privacy

-   No privileged Supabase writes from Android.
-   No service-role/database/provider/admin secrets in app resources,
    BuildConfig, source control or APK.
-   Do not log auth tokens, phone numbers, credentials or sensitive call
    transcript content.
-   Use synthetic customers and test contacts.
-   Use authenticated API requests according to the existing auth
    design; do not invent an insecure identity scheme.
-   Store only minimal cache. If auth tokens exist, use the project's
    approved secure storage approach.
-   Use HTTPS in hosted builds; local cleartext HTTP must be limited to
    an explicit debug configuration if unavoidable.
-   Validate all server response fields and handle unknown enum values
    safely.
-   Do not allow a forged push/Realtime payload to directly update
    authoritative payment state without a backend refetch.

------------------------------------------------------------------------

## 9. Testing requirements

Add tests appropriate to the existing project architecture.

### Unit tests

-   API DTO mapping and unknown enum handling.
-   ViewModel/UI state for each payment state.
-   `needs_trusted` and call labels are rendered from server fields.
-   Duplicate submit reuses one idempotency key.
-   Offline cancel keeps pending state and reuses key.
-   Stale response cannot overwrite newer version.
-   Amount boundary response rendering.

### Integration/manual tests

1.  Create a simulated payment; confirm it appears in app history after
    restart.
2.  Confirm the same payment appears in website queue when website is
    available.
3.  Create P1 hold and confirm the app does not mark it executed.
4.  Cancel online; show only the backend-confirmed outcome.
5.  Queue cancellation offline; allow server timer to expire; reconnect;
    show server's `STOPPED` state with timer explanation.
6.  Reconnect while hold is still active; retry cancellation with the
    same idempotency key.
7.  Trigger a 409 stale-version response; refetch and display current
    state.
8.  Confirm call mode label matches server `mode`.
9.  Confirm call result does not imply payment release.
10. Confirm ₹9,999 / ₹10,000 / ₹50,000 / ₹50,001 cases render according
    to server response.
11. Confirm app still builds and existing working flows remain intact.

------------------------------------------------------------------------

## 10. Antigravity implementation workflow

Follow this sequence and do not skip the inspection stage.

### Step A --- Inspect first

-   List project structure and identify entry activity, navigation,
    screens, ViewModels, repositories, networking, models, build files
    and current API/backend setup.
-   Build and run the existing app.
-   Report what currently works, what is missing, and which files will
    be changed.
-   Do not start a full rewrite before presenting this short audit.

### Step B --- Integrate API layer

-   Create/update typed models and repository methods using the actual
    backend OpenAPI/schema.
-   Configure base URL safely.
-   Add consistent handling for idempotency, versions, timeouts, 409s
    and offline state.

### Step C --- Upgrade screens incrementally

-   Home/payment entry and history.
-   Payment result/detail and hold.
-   Cancellation/offline state.
-   Call status.
-   Trusted-person status/settings only to the extent supported by API.
-   Loading/error/empty states and accessibility.

### Step D --- Verify

-   Run Gradle build and tests.
-   Fix compile errors and regressions.
-   Manually test one full payment workflow.
-   Report exact changed files, endpoints used, tests run, build result,
    and any backend endpoint/schema gaps.

### Step E --- Stop scope creep

Do not implement the website, ESP32 firmware, backend scoring engine,
new database migrations, real banking integration, or live voice
provider in this Android-only task. If a required backend endpoint is
missing, document it as a dependency rather than fabricating a separate
client-side solution.

------------------------------------------------------------------------

## 11. Definition of done

-   [ ] Existing project inspected and working functionality preserved.
-   [ ] App builds successfully.
-   [ ] Payment creation uses FastAPI and is idempotent.
-   [ ] History/details show persisted backend data.
-   [ ] All displayed states come from backend responses/refetches.
-   [ ] Risk explanation is understandable and non-accusatory.
-   [ ] Simulation label is prominent.
-   [ ] Cancellation offline/online semantics are correct.
-   [ ] Call mode comes from server record.
-   [ ] Trusted-person requirement is displayed from server, not
    calculated locally.
-   [ ] No privileged secrets are embedded in the app.
-   [ ] Tests cover stale versions, retry idempotency and threshold
    rendering.
-   [ ] No website/hardware/backend rewrite is included in this task.
-   [ ] Developer reports files changed, tests run and any missing
    backend contracts.

## Final instruction to the coding agent

Upgrade the existing Android app in place to become the LIRA v6.0
customer client. Preserve working code, use the actual FastAPI contract,
and treat backend-confirmed state as authoritative. Do not implement
website or ESP32 work in this task. Do not simulate successful server
actions locally. If an API capability is missing, report the dependency
instead of inventing a competing implementation.
