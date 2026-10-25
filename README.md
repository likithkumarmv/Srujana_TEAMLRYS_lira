# LIRA — Autonomous Fraud Radar & Tactical Physical Auth Platform

> **Problem Track F-01:** Financial Fraud and Transaction Risk Detection  
> **System Architecture:** Hybrid Mobile Terminal (Android Compose + NFC) + Web Investigation Console (React 18 + Vite) + Microservices Risk Engine (FastAPI) + Hardware Terminal (ESP32 RFID) + Cloud Database (Supabase PostgreSQL).  
> **Deployment Status:** 100% Autonomous, Production-Ready, Offline-Resilient Vertical Slice.

---

## 📑 Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [What the Application Does](#2-what-the-application-does)
3. [Android Mobile App: LIRA DEFENSE](#3-android-mobile-app-lira-defense)
4. [Web Investigation Console](#4-web-investigation-console)
5. [Backend Risk Engine & AI Services](#5-backend-risk-engine--ai-services)
6. [Hardware Security Terminals (NFC / RFID)](#6-hardware-security-terminals-nfc--rfid)
7. [Database & Single Source of Truth](#7-database--single-source-of-truth)
8. [Quickstart & Running Instructions](#8-quickstart--running-instructions)
9. [Demonstration & Walkthrough Script](#9-demonstration--walkthrough-script)

---

## 1. Executive Summary

**LIRA** is a next-generation defense platform engineered to eliminate catastrophic financial wire fraud, internal collusion, and account takeovers. Traditional fraud detection software merely flags suspicious transactions inside a remote cloud dashboard—often hours after funds have cleared offshore.

LIRA bridges **algorithmic risk intelligence** with **physical air-gapped authorization (Zero Trust)**:
- High-risk transactions (e.g. Rogue SWIFT MT103 batches, SIM-swap drain requests, mule pass-throughs) are intercepted autonomously.
- High-severity actions require a **physical physical tap from an authorized operator's ISO 14443-A NFC / RFID smartcard** before wires can be released.
- The entire system operates in a **100% offline-first, detachable state**—enabling tactical fraud analysts and bank supervisors to investigate threats and authorize clearances directly on field mobile terminals without reliance on tethered PCs or external servers.

---

## 2. What the Application Does

LIRA performs end-to-end fraud lifecycle mitigation through five synchronized operational pillars:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LIRA DEFENSE ECOSYSTEM                          │
├────────────────────┬────────────────────┬──────────────────────────────┤
│ 1. RISK RADAR      │ 2. PHYSICAL AUTH   │ 3. COGNITIVE INVESTIGATION   │
│ - Real-Time Scans  │ - ISO 14443-A NFC  │ - 8-Signal Scoring (0-100)   │
│ - SWIFT MT103 Inter│ - Tiers L1 to L4   │ - Transparent Point Rules    │
│ - SIM-Swap Inter   │ - Biometric Haptics│ - AI Voice Supplier Check    │
│ - Auto-Freeze Wire │ - Detachable App   │ - Gemini 1.5 Flash Copilot   │
├────────────────────┴────────────────────┴──────────────────────────────┤
│ 4. IMMUTABLE AUDIT TRAIL        │ 5. HYBRID ARCHITECTURE               │
│ - Microsecond event ledger      │ - Android Jetpack Compose Mobile App │
│ - Categories: AUTH, FRAUD, SYS  │ - React 18 + Vite Web Console        │
│ - Zero data loss offline storage│ - Python 3.13 FastAPI Backend API    │
└─────────────────────────────────┴──────────────────────────────────────┘
```

### Key Capabilities at a Glance:
1. **Intercepts Wire Fraud in Real Time:** Detects Business Email Compromise (BEC), rogue wire batches, structuring patterns, synthetic identity sweeps, and pass-through money mule funnels.
2. **Enforces Physical Smartcard Verification:** Overrides purely digital authentication with real-world NFC/RFID smartcard taps from verified Tier 1–4 personnel.
3. **Explains Every Risk Score (0–100):** No black-box guesses. Scores are calculated deterministically across 8 weighted signals with plain-English rationales.
4. **Verifies Counterparties Autonomously via AI Voice:** Calls suppliers independently to verify invoice bank details before large disbursements.
5. **Maintains Tamper-Evident Audit Trails:** Logs every badge scan, wire freeze, manual override, and clearance update.

---

## 3. Android Mobile App: LIRA DEFENSE

Located in `app/src/main/java/com/example/lira/` (compiled binary: `Lira-app-debug.apk`), this is the flagship military-grade tactical terminal.

### 3.1. Zero-Dependency & 100% Offline Resilience
- **Detachable From USB:** Requires zero active debugger, dev server, or PC connection. Once installed, it runs 100% standalone on Android 10 through Android 16.
- **Local Persistence:** Uses private flash storage (`SharedPreferences` / SQLite) ensuring all keycards, fraud cases, and audit logs persist through reboots and airplane mode.

### 3.2. Physical NFC Hardware Interrogation
- **ISO 14443-A Reader Engine:** Uses Android's low-level `NfcAdapter.enableReaderMode` to scan physical contactless smartcards, NFC fobs, and employee badges against the back of the device.
- **Live Hardware Telemetry:** Displays dynamic sensor status (`NFC SENSOR READY`, `NFC DISABLED`, or `NFC SIMULATOR ACTIVE`).
- **Tactile & Acoustic Confirmation:** Fires custom haptic vibration patterns (Success, Warning, Error, Tap) and hardware audio tones via `ToneGenerator`.

### 3.3. Keycard Lifecycle & Clearance Management (Tab 0: BADGES)
- **4 Operational Clearance Tiers:**
  - 🟢 **Tier L1 (Operator / General):** Emerald theme. Standard facility and low-risk clearance.
  - 🔵 **Tier L2 (Specialist / Officer):** Cyan theme. Transaction review and verification rights.
  - 🟣 **Tier L3 (Lead Supervisor / Admin):** Purple theme. High-value wire release authorization.
  - 🟡 **Tier L4 (Executive / Director):** Gold theme. Emergency SWIFT override and system management.
- **Holographic Keycard UI:** Displays embossed EMV smart chip graphics, operator avatar rings, monospace UID tokens, clearance pills, and real-time active/suspended badges.
- **Full Credential Operations:**
  - **Enroll:** Register newly detected or manual NFC tags with custom operator names, roles, and clearance.
  - **Edit:** Modify permissions, department, or tier instantly.
  - **Suspend / Activate:** 1-tap kill-switch to temporarily revoke badge clearance.
  - **Revoke:** Permanently wipe compromised credentials.

### 3.4. Autonomous Fraud Risk Radar (Tab 1: RADAR)
- **Dynamic Radar HUD:** Continuous 360-degree beam sweep animation with pulsing concentric range rings and active target counter.
- **Pre-Configured Threat Scenarios:**
  - *Rogue SWIFT MT103 Batch ($1,250,000 | Score 96 CRITICAL)* — Out-of-hours offshore clearing attempt.
  - *SIM-Swap OTP Bypass Drain ($82,400 | Score 82 HIGH)* — Carrier switch 18 mins prior to credential reset.
  - *Pass-Through Mule Ring ($320,000 | Score 89 CRITICAL)* — Rapid splitting into 16 instant neo-bank accounts.
  - *Synthetic Loan Identity Sweep ($115,000 | Score 75 HIGH)* — Fabricated SSN credit history batch.
- **Tactical Threat Actions:**
  - **Demand Physical NFC Auth:** Locks the transaction until an authorized operator physically taps an active L3/L4 keycard to the phone.
  - **Freeze Transaction:** Immediate halt on settlement with visual red lockout state.
  - **Release Transfer:** Verifies operator credentials and releases the wire to clearing.

### 3.5. Immutable Audit Ledger (Tab 2: AUDIT)
- **Tamper-Evident History:** Chronological log of every event with millisecond timestamps.
- **Instant Category Filtering:** Filter by `ALL`, `AUTH` (badge registrations/scans), `FRAUD` (threat alerts/freezes), or `SYSTEM` (database sync/resets).

### 3.6. Engine Diagnostics & Demo Controls (Tab 3: SYS)
- **Hardware Diagnostics:** Live inspection of NFC transceiver, local storage usage, and active session tokens.
- **Zero-Data Production Slate:** By default, launches in 100% clean-slate mode (0 fake cards, 0 mock cases).
- **Interactive `[⚡ DEMO]` / `[🗑️ CLEAR]` Mode:**
  - 1-tap button in the top header and hero radar card.
  - Instantly seeds 5 tiered holographic keycards and 4 critical fraud scenarios for live presentations.
  - Tapping `[🗑️ CLEAR]` completely wipes all data back to clean production zero.

---

## 4. Web Investigation Console

Located in `apps/web/`, built with **React 18**, **TypeScript**, and **Vite**.

- **Executive KPI Dashboard:** Real-time visibility into overall risk exposure ($), critical alert volume, and average risk score.
- **Investigation Workbench:**
  - Full breakdown of fired fraud signals with exact weight distributions (0–100 scale).
  - **Episode Relationship Network Graph:** Visual node diagram connecting suspicious accounts, IP addresses, phone numbers, and destination banks.
  - **Investigator Sign-off (Disposition):** Record official dispositions (`Confirmed Fraud`, `False Positive`, `Escalated`) with immutable investigator notes.
- **AI Calling Agent Integration:** Direct trigger to simulate or place live automated verification calls to supplier finance heads.
- **Gemini AI Copilot:** Instant synthesis of investigation leads, counterparty queries, and interview question generation.
- **Web NFC & Device Console:** Remote view and management of registered ESP32 terminals and physical badge registries.

---

## 5. Backend Risk Engine & AI Services

Located in `services/api/`, built with **Python 3.13** and **FastAPI**.

### 5.1. Deterministic 8-Signal Risk Engine
The engine computes an exact 0–100 risk score without opaque black-box drift:
1. `VELOCITY_SPIKE` (+25 pts): Transaction frequency exceeds 300% of rolling 30-day baseline.
2. `OFFSHORE_HIGH_RISK_JURISDICTION` (+20 pts): Wire routing to non-cooperative or sanctioned jurisdictions.
3. `NEW_COUNTERPARTY_HIGH_VALUE` (+20 pts): First-time beneficiary receiving greater than $50,000.
4. `OUT_OF_OPERATIONAL_HOURS` (+15 pts): Batch dispatched between 23:00 and 05:00 local corporate time.
5. `SIM_SWAP_VELOCITY` (+30 pts): Telco SIM-swap recorded within 48 hours of wire release request.
6. `BENFORD_ANOMALY` (+15 pts): Deviation in leading-digit numerical distribution.
7. `STRUCTURING_DETECTION` (+25 pts): Multiple transactions clustered just below regulatory reporting thresholds.
8. `SANCTION_ENTITY_MATCH` (+40 pts): Exact or fuzzy match against international watchlists.

### 5.2. Autonomous AI Calling Agent
- Automated voice dispatch to supplier finance contacts.
- Tests legitimacy of recent account/routing number changes.
- Transcribes and parses audio responses into structured findings (`Explicit Denial`, `Confirmed Authorized`, `Unreachable`).

### 5.3. Google Gemini 1.5 Integration
- Synthesizes complex multi-hop transaction graphs into natural-language forensic summaries.
- Auto-generates targeted interview questions for compliance officers.

---

## 6. Hardware Security Terminals (NFC / RFID)

Located in `firmware/esp32_lira_terminal/`.

- **Platform:** ESP32 DevKit V1 (Espressif ESP-IDF / Arduino C++).
- **Peripherals:**
  - **RC522 13.56MHz RFID Reader:** Scans ISO 14443-A smartcards and tags.
  - **ILI9341 320×240 Color TFT LCD:** Renders real-time transaction approval prompts, risk levels, and clearance verification.
  - **5-Button Tactical Console:** Hardware buttons for `FREEZE`, `AUTHORIZE`, `DEMAND NFC`, `NEXT`, and `BACK`.
  - **Piezo Buzzer & Indicator LEDs:** Multi-tone acoustic alerts for approved vs. blocked transactions.

---

## 7. Database & Single Source of Truth

Located in `supabase/` (**PostgreSQL** with Row Level Security):

- `nfc_cards`: Registered smartcards, cryptographic UIDs, operator names, clearances (L1–L4), and status.
- `transactions`: Core transaction ledger with timestamps, amounts, currencies, and counterparties.
- `risk_episodes`: Clustered transaction groups flagged for investigation.
- `risk_signals`: Detailed signal firings linked to specific episodes.
- `audit_logs`: Append-only compliance ledger recording every terminal tap, freeze, and override.
- `suppliers`: Supplier directory with verified contact phone numbers for AI verification.

---

## 8. Quickstart & Running Instructions

### 8.1. Running the Android App Standalone (Recommended)
The app is already compiled and installed on your connected device.
1. Disconnect the USB cable if desired.
2. Open **Lira Defense** from your phone's app drawer.
3. The app opens in **Clean Slate Mode (0 fake data)**.
4. Tap **`⚡ DEMO`** at the top right to instantly load test credentials and fraud cases.
5. Touch any physical NFC tag to the phone's back to test live smartcard detection.

### 8.2. Starting the Backend API (FastAPI)
```powershell
# Open a PowerShell terminal
$py = "C:\Users\sujee\AppData\Local\Programs\Python\Python313\python.exe"
cd services/api
& $py -m uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`

### 8.3. Starting the Web Investigation Console
```powershell
# Open a second PowerShell terminal
$nodeDir = "C:\Users\sujee\AppData\Local\Programs\nodejs"
$env:Path = "$nodeDir;" + $env:Path
cd apps/web
npm run dev
```
- Web Console: `http://localhost:5173`

### 8.4. Running the Test Suite
```powershell
$py = "C:\Users\sujee\AppData\Local\Programs\Python\Python313\python.exe"
cd services/api
& $py -m pytest app/tests -v
```
All 11 unit tests covering deterministic risk scoring and NFC validation will execute and pass.

---

## 9. Demonstration & Walkthrough Script

### Scenario A: Clean Slate & Live Demo Toggle
1. Launch **Lira Defense** on mobile. Note that all statistics show `0` (Zero Fake Data).
2. Tap **`⚡ DEMO`** in the top navigation bar.
3. Instantly observe:
   - `TOTAL BADGES` updates to `5` with holographic operator cards (Sarah L3, Marcus L2, Priya L1, etc.).
   - `RADAR` alerts update to `4` high-risk intercepted wire cases.
   - Audit trail records the initial authorization session.
4. Tap **`🗑️ CLEAR`** in the top bar to wipe everything back to zero whenever a clean state is required.

### Scenario B: Physical NFC Tap Authorization
1. On the mobile terminal or Web Console, tap **`+ Issue Badge`**.
2. Tap a physical contactless card to the back of the phone.
3. The phone's NFC hardware reads the tag UID, plays an audio chirrup, and vibrates.
4. Assign the operator name and clearance **Tier L3**, then tap **Enroll Badge**.
5. The badge appears in the holographic ledger with an active EMV chip design.

### Scenario C: Wire Fraud Interception & Freeze
1. In the **RADAR** tab, select the **Rogue SWIFT MT103 Batch ($1,250,000)**.
2. Review the autonomous trigger: *Anomalous high-value batch dispatch detected outside operational trading window*.
3. Tap **🔑 Demand NFC** — the transaction enters a locked state requiring physical badge authorization.
4. Tap **⛔ Freeze** — the wire settlement is halted immediately, and a `CRITICAL` audit log entry is recorded in the immutable ledger.

---

**Built with pride for high-stakes financial defense and autonomous fraud mitigation.**
