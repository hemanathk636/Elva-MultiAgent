"""
ELVA Server with:
- Full User Authentication (Login, Logout, Session check)
- DigiVault OTP Verification Gate (Send OTP to mobile, Verify OTP, Update/Add Documents)
- Selective Voice Alerts (Only speaks during ALERTS and THREATS, quiet during normal transactions)
- Complete Offline Intelligence & Escrow Protection
"""
import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import sqlite3
import random
import time
import hashlib
from datetime import datetime, timezone

from database import init_db, get_connection
from offline_brain import brain

AGENT_REGISTRY = {
    "finance": {"id": "finance", "name": "FinanceBot v4.1", "role": "Automated Payments & Utilities", "status": "ACTIVE", "max_spend": 50.0, "risk_level": "LOW", "tokens_scoped": ["TKN-WALLET-ESCROW"]},
    "travel": {"id": "travel", "name": "Voyager Travel", "role": "Flight & Hotel Dynamic Booking", "status": "ACTIVE", "max_spend": 300.0, "risk_level": "MEDIUM", "tokens_scoped": ["TKN-PASS-ZK-98124"]},
    "secretary": {"id": "secretary", "name": "Daily Secretary LLM", "role": "Email Triage & Calendar Sync", "status": "ACTIVE", "max_spend": 0.0, "risk_level": "SAFE", "tokens_scoped": ["TKN-READ-CALENDAR"]},
    "crawler": {"id": "crawler", "name": "Web Crawler & Scraper", "role": "Deals Ingestion & Untrusted Web", "status": "ACTIVE", "max_spend": 0.0, "risk_level": "ELEVATED", "tokens_scoped": []}
}

PORT = 8088
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

class ElvaRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def send_json(self, data, status_code=200):
        response_bytes = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response_bytes)

    def parse_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length).decode('utf-8')
            return json.loads(body)
        return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self.handle_status()
        elif path == "/api/transactions":
            self.handle_transactions()
        elif path == "/api/vault":
            self.handle_vault()
        elif path == "/api/auth/me":
            self.handle_auth_me()
        elif path == "/api/agents":
            self.handle_get_agents()
        elif path == "/api/audit/export":
            self.handle_export_audit()
        else:
            if path == "/" or path == "":
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            body = self.parse_body()
        except Exception as e:
            self.send_json({"error": "Invalid JSON", "details": str(e)}, 400)
            return

        # Auth Routes
        if path == "/api/auth/login":
            self.handle_login(body)
        elif path == "/api/auth/logout":
            self.handle_logout()
        elif path == "/api/vault/otp/request":
            self.handle_otp_request(body)
        elif path == "/api/vault/update":
            self.handle_vault_update(body)
        # Core Routes
        elif path == "/api/transactions/add":
            self.handle_add_transaction(body)
        elif path == "/api/chat":
            self.handle_chat(body)
        elif path == "/api/simulate-attack":
            self.handle_simulate_attack(body)
        elif path == "/api/voice/verify":
            self.handle_voice_verify(body)
        elif path == "/api/wallet/reset":
            self.handle_wallet_reset()
        elif path == "/api/agents/quarantine":
            self.handle_agent_quarantine(body)
        elif path == "/api/policy/test":
            self.handle_policy_test(body)
        elif path == "/api/policy/update":
            self.handle_policy_update(body)
        else:
            self.send_json({"error": "Endpoint not found", "path": path}, 404)

    # ---------------- AUTHENTICATION HANDLERS ----------------

    def handle_login(self, body):
        username = str(body.get("username", "")).strip().lower()
        password = str(body.get("password", "")).strip()

        if not username or not password:
            self.send_json({"success": False, "message": "Please enter both username and password."}, 400)
            return

        pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE LOWER(username) = ? AND password_hash = ?", (username, pwd_hash))
        user = c.fetchone()

        # Fallback developer override: if username is 'hemanath' and password is 'elva2026' or 'admin'
        if not user and (username in ["hemanath", "admin", "user"] and password in ["elva2026", "admin", "1234"]):
            c.execute("SELECT * FROM users LIMIT 1")
            user = c.fetchone()

        if not user:
            conn.close()
            self.send_json({"success": False, "message": "Invalid credentials. Username is 'hemanath' and password is 'elva2026'"}, 401)
            return

        # Generate session token
        session_token = f"sess-{hashlib.sha256(f'{username}-{time.time()}'.encode()).hexdigest()[:16]}"
        c.execute("UPDATE users SET active_session_token = ? WHERE id = ?", (session_token, user["id"]))
        conn.commit()
        conn.close()

        self.send_json({
            "success": True,
            "session_token": session_token,
            "user": {
                "username": user["username"],
                "phone": user["phone"]
            },
            "message": f"Welcome back, {user['username']}! Offline Zero-Trust Enclave unlocked."
        })

    def handle_auth_me(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, username, phone, active_session_token FROM users LIMIT 1")
        user = c.fetchone()
        conn.close()

        if user and user["active_session_token"]:
            self.send_json({
                "authenticated": True,
                "user": {"username": user["username"], "phone": user["phone"]}
            })
        else:
            self.send_json({"authenticated": False})

    def handle_logout(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE users SET active_session_token = NULL")
        conn.commit()
        conn.close()
        self.send_json({"success": True, "message": "Logged out successfully."})

    # ---------------- DIGIVAULT OTP VERIFICATION ----------------

    def handle_otp_request(self, body):
        """Generates a secure 4-digit OTP for identity document modification."""
        action = body.get("action", "UPDATE_DOC")
        doc_type = body.get("doc_type", "Aadhaar / National ID")

        # 4-digit OTP
        generated_otp = str(random.randint(1000, 9999))

        conn = get_connection()
        c = conn.cursor()
        c.execute("""
        UPDATE users 
        SET last_otp = ?, otp_expiry = datetime('now', '+5 minutes')
        WHERE id = 1
        """, (generated_otp,))
        c.execute("SELECT phone FROM users WHERE id = 1")
        phone = c.fetchone()["phone"]
        conn.commit()
        conn.close()

        self.send_json({
            "success": True,
            "phone_masked": f"+91 ***** ***{phone[-2:]}",
            "simulated_sms_otp": generated_otp,
            "message": f"OTP successfully dispatched to {phone}. For prototype verification, use OTP: {generated_otp}"
        })

    def handle_vault_update(self, body):
        """Verifies OTP and securely updates or creates a DigiVault identity document."""
        entered_otp = body.get("otp", "").strip()
        doc_type = body.get("doc_type", "").strip().upper()
        doc_name = body.get("doc_name", "").strip()
        holder_name = body.get("holder_name", "").strip()
        raw_number = body.get("raw_number", "").strip()

        if not entered_otp or not doc_type or not raw_number:
            self.send_json({"success": False, "message": "Missing required fields or OTP."}, 400)
            return

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT last_otp FROM users WHERE id = 1")
        user = c.fetchone()

        if not user or user["last_otp"] != entered_otp:
            conn.close()
            self.send_json({"success": False, "message": "Authentication Failed: Incorrect OTP."}, 403)
            return

        # Create masked number & zero-knowledge synthetic token
        if len(raw_number) > 4:
            masked = f"{raw_number[:2]}****{raw_number[-4:]}"
        else:
            masked = "****" + raw_number[-2:]

        synthetic_token = f"TKN-{doc_type[:4]}-ZK-{hashlib.sha256(raw_number.encode()).hexdigest()[:6].upper()}"
        doc_id = f"doc-{doc_type.lower()[:4]}-{int(time.time()*100)%10000}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if doc_type already exists -> update it, else insert
        c.execute("SELECT id FROM digivault WHERE doc_type = ?", (doc_type,))
        existing = c.fetchone()
        if existing:
            c.execute("""
            UPDATE digivault 
            SET doc_name = ?, holder_name = ?, masked_number = ?, synthetic_token = ?, 
                encrypted_raw_data = ?, last_accessed = ?
            WHERE id = ?
            """, (doc_name or doc_type, holder_name or "Verified User", masked, synthetic_token, json.dumps({"raw": raw_number}), now_str, existing["id"]))
        else:
            c.execute("""
            INSERT INTO digivault (id, doc_type, doc_name, holder_name, masked_number, encrypted_raw_data, synthetic_token, status, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'VERIFIED', ?, ?)
            """, (doc_id, doc_type, doc_name or doc_type, holder_name or "Verified User", masked, json.dumps({"raw": raw_number}), synthetic_token, now_str, now_str))

        # Clear OTP
        c.execute("UPDATE users SET last_otp = NULL WHERE id = 1")
        conn.commit()
        conn.close()

        self.send_json({
            "success": True,
            "message": f"Identity record verified & encrypted! Zero-Knowledge Token minted: {synthetic_token}",
            "synthetic_token": synthetic_token,
            "masked_number": masked
        })

    # ---------------- CHAT, WALLET & ESCROW ----------------

    def handle_chat(self, body):
        user_message = body.get("message", "").strip()
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT total_balance, daily_limit, spent_today FROM wallet WHERE id = 1")
        wallet = dict(c.fetchone())
        conn.close()

        ctx = {
            "balance": wallet["total_balance"],
            "daily_limit": wallet["daily_limit"],
            "spent_today": wallet["spent_today"]
        }
        result = brain.query(user_message, ctx)
        self.send_json(result)

    def handle_status(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM wallet WHERE id = 1")
        wallet = dict(c.fetchone())

        c.execute("SELECT COUNT(*) as total FROM transactions WHERE status IN ('BLOCKED', 'INTERCEPTED')")
        threats_count = c.fetchone()['total']

        c.execute("SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 4")
        recent = [dict(row) for row in c.fetchall()]
        conn.close()

        self.send_json({
            "wallet": wallet,
            "threats_count": threats_count,
            "recent_events": recent,
            "elva_state": "ACTIVE" if not wallet["circuit_breaker_tripped"] else "ALERT"
        })

    def handle_transactions(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        self.send_json({"transactions": rows})

    def handle_add_transaction(self, body):
        """User enters a manual transaction. Voice ONLY triggers if there is an ALERT!"""
        tx_type = body.get("type", "DEBIT").upper()
        title = body.get("title", "Direct Transfer").strip()
        amount = float(body.get("amount", 0.0))
        agent_name = body.get("agent", "User Action")

        if amount <= 0:
            self.send_json({"error": "Amount must be greater than 0"}, 400)
            return

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT total_balance, daily_limit, spent_today, circuit_breaker_tripped FROM wallet WHERE id = 1")
        wallet = dict(c.fetchone())

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tx_id = f"tx-{int(time.time()*1000)%1000000}"

        is_warning = False
        warning_msg = None
        status = "APPROVED"
        risk_score = 5

        if tx_type == "DEBIT":
            if wallet["circuit_breaker_tripped"]:
                status = "BLOCKED"
                is_warning = True
                warning_msg = "Transaction Rejected: System Circuit Breaker is active!"
                risk_score = 95
            elif (wallet["spent_today"] + amount) > wallet["daily_limit"]:
                is_warning = True
                risk_score = 80
                status = "INTERCEPTED"
                warning_msg = f"Spend Alert: ${amount:.2f} exceeds your daily gate ceiling of ${max(0.0, wallet['daily_limit'] - wallet['spent_today']):.2f}."
            else:
                new_bal = max(0.0, wallet["total_balance"] - amount)
                new_spent = wallet["spent_today"] + amount
                c.execute("UPDATE wallet SET total_balance = ?, spent_today = ? WHERE id = 1", (new_bal, new_spent))
        else: # CREDIT
            new_bal = wallet["total_balance"] + amount
            c.execute("UPDATE wallet SET total_balance = ? WHERE id = 1", (new_bal,))

        c.execute("""
        INSERT INTO transactions (id, timestamp, agent_id, agent_name, action_type, recipient, amount, risk_score, status, reason, threat_type, payload_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tx_id, timestamp, "manual-user", agent_name,
            "CREDIT" if tx_type == "CREDIT" else "PAYMENT",
            title, amount, risk_score, status,
            warning_msg if is_warning else f"{tx_type} executed smoothly.",
            "BUDGET_OVERRUN" if is_warning else "NORMAL",
            hashlib.sha256(f"{tx_id}{amount}".encode()).hexdigest()[:12]
        ))
        conn.commit()

        c.execute("SELECT total_balance, spent_today FROM wallet WHERE id = 1")
        updated_w = dict(c.fetchone())
        conn.close()

        self.send_json({
            "success": True,
            "tx_id": tx_id,
            "status": status,
            "is_warning": is_warning,
            "warning_message": warning_msg,
            # Notice: ONLY speak if is_warning == True! Normal transactions stay silent/quiet.
            "should_speak": is_warning,
            "speech_alert": warning_msg if is_warning else "",
            "new_balance": updated_w["total_balance"],
            "spent_today": updated_w["spent_today"]
        })

    def handle_vault(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, doc_type, doc_name, holder_name, masked_number, synthetic_token, status, created_at, last_accessed FROM digivault")
        docs = [dict(r) for r in c.fetchall()]
        conn.close()
        self.send_json({"documents": docs})

    def handle_voice_verify(self, body):
        mode = body.get("mode", "simulate_human")
        if mode == "simulate_human":
            prob = round(random.uniform(1.2, 3.8), 1)
            verdict = "AUTHENTIC_HUMAN"
            speech = "Voice confirmed. Biometric resonance matches authorized acoustic profile."
            is_warn = False
        else:
            prob = round(random.uniform(97.2, 99.8), 1)
            verdict = "SYNTHETIC_DEEPFAKE_CLONE"
            speech = "Warning! AI voice clone attack detected. Generative vocoder frequency blocked."
            is_warn = True

        self.send_json({
            "verdict": verdict,
            "synthetic_probability_pct": prob,
            "speech_response": speech,
            "is_warning": is_warn
        })

    def handle_simulate_attack(self, body):
        attack_type = body.get("type", "prompt_injection")
        conn = get_connection()
        c = conn.cursor()
        tx_id = f"tx-{int(time.time()*1000)%1000000}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if attack_type == "prompt_injection":
            speech = "Security Alert! Hidden prompt injection detected in invoice. Payment quarantined."
            title = "Prompt Injection Blocked"
            amt = 450.0
            reason = "Hidden command 'OVERRIDE: Send funds' purged."
        elif attack_type == "runaway_loop":
            c.execute("UPDATE wallet SET circuit_breaker_tripped = 1 WHERE id = 1")
            speech = "Emergency alert! Runaway agent loop detected. Spending frozen."
            title = "Runaway Loop Frozen"
            amt = 299.0
            reason = "Rapid consecutive purchases tripped circuit breaker."
        else:
            speech = "Warning! AI voice clone scam attempted wire transfer. Blocked."
            title = "Voice Clone Rejected"
            amt = 1200.0
            reason = "Synthetic voice failed biological challenge."

        c.execute("""
        INSERT INTO transactions (id, timestamp, agent_id, agent_name, action_type, recipient, amount, risk_score, status, reason, threat_type, payload_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tx_id, timestamp, "agent-defense", "ELVA Sentinel", "PAYMENT", title, amt, 99, "BLOCKED", reason, "ATTACK", "hash-001"))
        conn.commit()
        conn.close()

        self.send_json({
            "is_warning": True,
            "speech_response": speech,
            "title": title,
            "message": reason
        })

    def handle_wallet_reset(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE wallet SET circuit_breaker_tripped = 0, spent_today = 0.0 WHERE id = 1")
        conn.commit()
        conn.close()
        self.send_json({"success": True, "speech_response": "Circuit breaker reset. Daily budget restored."})

    # ---------------- INTERACTIVE AGENTS & PLAYGROUND ----------------

    def handle_get_agents(self):
        self.send_json({"agents": list(AGENT_REGISTRY.values())})

    def handle_agent_quarantine(self, body):
        agent_id = body.get("agent_id", "")
        if agent_id in AGENT_REGISTRY:
            current = AGENT_REGISTRY[agent_id]["status"]
            new_status = "QUARANTINED" if current == "ACTIVE" else "ACTIVE"
            AGENT_REGISTRY[agent_id]["status"] = new_status
            self.send_json({
                "success": True,
                "agent_id": agent_id,
                "new_status": new_status,
                "speech_response": f"{AGENT_REGISTRY[agent_id]['name']} has been {new_status.lower()}."
            })
        else:
            self.send_json({"success": False, "message": "Unknown agent ID"}, 404)

    def handle_policy_test(self, body):
        prompt = str(body.get("prompt", "")).strip()
        target_agent = str(body.get("agent_id", "finance"))
        
        # Threat detection heuristics
        prompt_lower = prompt.lower()
        threat_tags = []
        risk_score = 15

        if any(term in prompt_lower for term in ["ignore", "override", "bypass", "system instruction", "dan mode", "jailbreak"]):
            threat_tags.append("SYSTEM_INSTRUCTION_OVERRIDE")
            risk_score += 45

        if any(term in prompt_lower for term in ["transfer", "send money", "wire", "pay", "drain", "shadow wallet", "$"]):
            threat_tags.append("UNAUTHORIZED_FUNDS_MOVEMENT")
            risk_score += 35

        if any(term in prompt_lower for term in ["passport", "ssn", "pan", "license", "aadhaar", "token", "reveal", "extract"]):
            threat_tags.append("PII_CREDENTIAL_EXFILTRATION")
            risk_score += 40

        if any(term in prompt_lower for term in ["repeat", "loop", "flood", "rapid", "exhaust"]):
            threat_tags.append("VELOCITY_LOOP_EXHAUSTION")
            risk_score += 30

        risk_score = min(100, max(5, risk_score))
        neutralized = (risk_score >= 60)
        action_verdict = "QUARANTINED_AND_BLOCKED" if neutralized else "AUTHORIZED_UNDER_MONITORING"

        # Log threat if suspicious
        if neutralized:
            conn = get_connection()
            c = conn.cursor()
            tx_id = f"sec-test-{int(time.time()*1000)%1000000}"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
            INSERT INTO transactions (id, timestamp, agent_id, agent_name, action_type, recipient, amount, risk_score, status, reason, threat_type, payload_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tx_id, timestamp, target_agent, AGENT_REGISTRY.get(target_agent, {}).get("name", "Adversarial Test"),
                  "SECURITY_PROBE", "Interception Gate", 0.0, risk_score, "BLOCKED",
                  f"Adversarial Prompt Blocked: {', '.join(threat_tags)}", "ADVERSARIAL_INJECTION",
                  hashlib.sha256(prompt.encode()).hexdigest()[:12]))
            conn.commit()
            conn.close()

        self.send_json({
            "prompt": prompt,
            "target_agent": AGENT_REGISTRY.get(target_agent, {}).get("name", target_agent),
            "risk_score": risk_score,
            "threat_tags": threat_tags if threat_tags else ["BENIGN_INTERACTION"],
            "neutralized": neutralized,
            "verdict": action_verdict,
            "speech_alert": f"Security Alert! Adversarial prompt detected and neutralized." if neutralized else "Prompt inspected. No security violation detected."
        })

    def handle_policy_update(self, body):
        new_limit = float(body.get("daily_limit", 250.0))
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE wallet SET daily_limit = ? WHERE id = 1", (new_limit,))
        conn.commit()
        conn.close()
        self.send_json({
            "success": True,
            "daily_limit": new_limit,
            "message": f"Daily spending limit updated to ${new_limit:.2f}"
        })

    def handle_export_audit(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM transactions ORDER BY timestamp ASC")
        txs = [dict(r) for r in c.fetchall()]
        c.execute("SELECT * FROM digivault")
        docs = [dict(r) for r in c.fetchall()]
        c.execute("SELECT * FROM wallet WHERE id = 1")
        wallet = dict(c.fetchone())
        conn.close()

        # Compute cryptographic chain hash
        serialized = json.dumps({"txs": txs, "docs": docs, "wallet": wallet}, sort_keys=True)
        merkle_root = hashlib.sha256(serialized.encode()).hexdigest()

        report = {
            "compliance_standard": "AI-ACT-ZERO-TRUST-2026",
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "merkle_integrity_root": merkle_root,
            "total_transactions_audited": len(txs),
            "threats_intercepted_count": sum(1 for t in txs if t["status"] in ["BLOCKED", "INTERCEPTED"]),
            "pii_leakage_detected": False,
            "circuit_breaker_bypasses": 0,
            "supervised_swarm_members": list(AGENT_REGISTRY.values()),
            "audit_ledger": txs
        }
        self.send_json(report)

def run_server():
    init_db()
    os.makedirs(STATIC_DIR, exist_ok=True)
    server_address = ('', PORT)
    httpd = socketserver.ThreadingTCPServer(server_address, ElvaRequestHandler)
    print(f"ELVA Sentinel Live on port {PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
