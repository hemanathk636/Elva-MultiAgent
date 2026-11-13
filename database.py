"""
ELVA Database Layer with User Authentication (PIN/Passcode, Session tokens, Simulated OTP)
and Dynamic DigiVault Document addition/updates.
"""
import sqlite3
import json
import os
import hashlib
import random
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "elva_data.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # 1. User Authentication table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        phone TEXT NOT NULL,
        active_session_token TEXT,
        last_otp TEXT,
        otp_expiry TEXT
    )
    """)

    # 2. Wallet & Limits
    c.execute("""
    CREATE TABLE IF NOT EXISTS wallet (
        id INTEGER PRIMARY KEY,
        total_balance REAL NOT NULL,
        daily_limit REAL NOT NULL,
        spent_today REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'USD',
        circuit_breaker_tripped INTEGER NOT NULL DEFAULT 0,
        last_reset_date TEXT NOT NULL
    )
    """)

    # 3. DigiVault documents
    c.execute("""
    CREATE TABLE IF NOT EXISTS digivault (
        id TEXT PRIMARY KEY,
        doc_type TEXT NOT NULL,
        doc_name TEXT NOT NULL,
        holder_name TEXT NOT NULL,
        masked_number TEXT NOT NULL,
        encrypted_raw_data TEXT NOT NULL,
        synthetic_token TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_accessed TEXT
    )
    """)

    # 4. Transactions
    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        action_type TEXT NOT NULL,
        recipient TEXT NOT NULL,
        amount REAL NOT NULL,
        risk_score INTEGER NOT NULL,
        status TEXT NOT NULL,
        reason TEXT NOT NULL,
        threat_type TEXT,
        payload_hash TEXT NOT NULL
    )
    """)

    # 5. Seed default demo user if not present
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        default_pwd_hash = hashlib.sha256(b"elva2026").hexdigest()
        c.execute("""
        INSERT INTO users (id, username, password_hash, phone, active_session_token, last_otp, otp_expiry)
        VALUES (1, 'hemanath', ?, '+91 98765 43210', 'token-demo-active', '4829', datetime('now', '+10 minutes'))
        """, (default_pwd_hash,))

    # Seed wallet if empty
    c.execute("SELECT COUNT(*) FROM wallet")
    if c.fetchone()[0] == 0:
        c.execute("""
        INSERT INTO wallet (id, total_balance, daily_limit, spent_today, currency, circuit_breaker_tripped, last_reset_date)
        VALUES (1, 14250.00, 250.00, 42.50, 'USD', 0, date('now'))
        """)

    # Seed initial vault docs if empty
    c.execute("SELECT COUNT(*) FROM digivault")
    if c.fetchone()[0] == 0:
        sample_docs = [
            ("doc-pass-01", "PASSPORT", "International Passport", "Hemanath K.", "Z****8912", json.dumps({"num": "Z89124018"}), "TKN-PASS-ZK-98124", "VERIFIED", "2026-01-10 10:00:00", None),
            ("doc-dl-02", "DRIVERS_LICENSE", "Driver's License & Real ID", "Hemanath K.", "DL-****-5521", json.dumps({"num": "DL-9821-5521"}), "TKN-DRIV-ZK-55210", "VERIFIED", "2026-02-15 11:30:00", None),
            ("doc-tax-03", "TAX_RECORD", "Federal Tax Return & PAN/SSN", "Hemanath K.", "***-**-6789", json.dumps({"num": "ABCDE6789F"}), "TKN-TAXX-ZK-67899", "LOCKED", "2026-03-01 16:45:00", None)
        ]
        c.executemany("INSERT INTO digivault VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_docs)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
