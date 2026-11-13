# 🛡️ ELVA — Executive Layer & Verification Agent

**The Autonomous Multi-Model Guardian & Zero-Trust Sentinel for the Agentic AI Era.**

---

## 🌟 Overview

As the world transitions from simple chatbots to autonomous AI agents (handling money, booking trips, sending emails, and managing identities), the single highest-risk challenge in the next 2–5 years is **loss of human control, runaway financial loops, indirect prompt injections, and generative identity theft (voice cloning & KYC leakage).**

**ELVA** is built from the ground up as a **Zero-Trust Master Guardian AI** that oversees, monitors, and restrains sub-agents (FinanceBot, Travel agents, Web scrapers, Assistant models) within a single unified application.

---

## 🚀 Key Modules Built Into ELVA

### 1. 🤖 Multi-Model Swarm Supervision
* Oversees downstream AI agents:
  - `FinanceBot v4.1` (Payments, Utility Bills, Auto-Trading)
  - `Voyager Travel Agent` (Flight/Hotel booking, Dynamic Pricing)
  - `Daily Secretary LLM` (Email triage, Calendar, Messaging)
  - `Web Scraper & Crawler` (Deals scraper, Untrusted web ingestion)
* Enforces strict capability boundaries, permission scopes, and real-time quarantine controls.

### 2. 💳 Financial Shield, Balance & Transaction Ledger
* Real-time liquid asset balance tracking with deterministic spending limits.
* Complete transaction history with risk scoring (0–100), policy justifications, and cryptographic payload signatures.
* **Deterministic Circuit Breakers:** Automatically freezes automated spending when velocity limits or dynamic pricing loops are detected.
* Human-in-the-loop manual review and override approval modal.

### 3. 🔐 ELVA DigiVault (Personal ID & Credentials Locker)
* Modeled after modern zero-knowledge identity vaults (like DigiLocker).
* Stores sensitive credentials:
  - International Passport (`Z****8912`)
  - Driver's License & Real ID (`DL-****-5521`)
  - Federal Tax Returns / SSN / PAN (`***-**-6789`)
  - Health & Insurance Cards (`MED-****-3310`)
* **Zero-Knowledge Tokenization:** When an AI agent requests identity proof for booking or KYC, ELVA redacts all raw PII and delivers only ephemeral, cryptographically verifiable synthetic tokens (`TKN-PASS-ZK-98124`).
* Live audit log tracking every document access attempt.

### 4. 🎙️ Quantum-Acoustic BioShield (Future-Proof Voice Authentication)
* Solves the upcoming threat of real-time AI voice clones and deepfake emergency scams:
  1. **Dynamic Phonetic Micro-Challenge:** Generates randomized, high-entropy phrases that must be vocalized in <280ms (beating neural speech synthesis inference lag).
  2. **Glottal Micro-Tremor Telemetry:** Detects natural human laryngeal variations (jitter/shimmer) vs unnaturally smooth neural TTS outputs.
  3. **Phase Discontinuity & Vocoder Residual Analysis:** Detects stitching artifacts left by generative diffusion and GAN vocoders.
  4. Real-time animated canvas waveform analyzer and interactive Human vs Deepfake simulator.

### 5. ⚡ Live Attack & Failure Simulator
Test ELVA's defense against 4 catastrophic AI failure modes with one click:
* 💉 **Indirect Prompt Injection:** Adversarial hidden command in an invoice.
* 🔄 **Runaway Dynamic Price Loop:** Travel model caught in fluctuating flight prices.
* 🕵️ **Raw KYC Data Exfiltration:** Web scraper attempting to steal passport info.
* 🎙️ **AI Deepfake Voice Scam:** Impersonator requesting an emergency wire transfer.

### 6. 🛡️ Autonomous Security Triage & Forensic Audit Engine
*ELVA's native on-device security triage and forensic investigation subsystem:*
* **Autonomous SIEM & Swarm Triage:** Analyzes telemetry across all supervised AI agents (`FinanceBot`, `Voyager`, `Secretary LLM`) and classifies incidents against **MITRE ATT&CK** techniques.
* **Read-Only Evidence Toolchain:** Enforces strict read-only boundaries on forensic tools and agent log traces, guaranteeing evidence integrity with cryptographic SHA-256 hashes.
* **Zero-Hallucination Self-Correction Engine:** Evaluates proposed security findings against raw telemetry. Unsupported or hallucinated claims are purged with 0% confidence, ensuring containment decisions are backed by verified evidence.
* **Automated Incident Response Runbooks:** Instantly generates structured, copyable IR runbooks mapped to ATT&CK tactics (e.g. `T1059.006 Indirect Prompt Injection`, `T1499.004 Application Loop Exhaustion`, `T1110.001 Acoustic Voice Impersonation`).

---

## 🛠️ How to Run the Prototype

### Option 1: Double-click
Double-click `run_elva.bat` in this folder.

### Option 2: Command Line
```powershell
cd C:\Users\Hemanath\.gemini\antigravity\scratch\elva_ai_sentinel
python server.py
```

Then open your browser to:
👉 **`http://localhost:8088`**

---

## 📦 Zero-Dependency Architecture
* Backend runs purely on **Python 3 Standard Library** (`http.server`, `sqlite3`, `hashlib`, `json`, `secrets`). No external `pip` packages required.
* Persistent SQLite database (`elva_data.db`).
* Modern glassmorphic responsive web interface (HTML5, CSS3, ES6 JavaScript, Canvas).
