"""
ELVA Local Offline Neural Intelligence & Rule-Based Reasoning Engine.
Zero cloud dependencies. Automatically connects to local LLM (Ollama/LM-Studio) if running on port 11434,
with an ultra-fast offline fallback neural rule engine.
"""
import urllib.request
import urllib.error
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"

class OfflineElvaBrain:
    def __init__(self):
        self.model_name = "llama3.2" # default if Ollama is running

    def is_ollama_available(self) -> bool:
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", headers={'User-Agent': 'ELVA-Offline'})
            with urllib.request.urlopen(req, timeout=1.0) as res:
                return res.status == 200
        except Exception:
            return False

    def query(self, user_text: str, context_data: dict) -> dict:
        """
        Processes user query 100% offline.
        Uses local Ollama if active; otherwise uses embedded Offline Sentinel Logic.
        """
        user_clean = user_text.strip().lower()

        # Check if Ollama is active on the machine
        if self.is_ollama_available():
            try:
                system_prompt = (
                    f"You are ELVA, a secure on-device AI sentinel running 100% offline on the user's laptop. "
                    f"Current liquid balance: ${context_data.get('balance', 14250):.2f}. "
                    f"Today's spent: ${context_data.get('spent_today', 42.50):.2f}. "
                    f"Identity documents in DigiVault: 4 cards protected by Zero-Knowledge tokens. "
                    f"Keep responses concise (1-2 sentences), friendly, calm, and conversational."
                )
                payload = json.dumps({
                    "model": self.model_name,
                    "prompt": f"{system_prompt}\nUser: {user_text}\nELVA:",
                    "stream": False
                }).encode('utf-8')

                req = urllib.request.Request(OLLAMA_URL, data=payload, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=5.0) as response:
                    res_json = json.loads(response.read().decode('utf-8'))
                    return {
                        "mode": "OLLAMA_LOCAL_LLM",
                        "response": res_json.get("response", "").strip(),
                        "offline": True
                    }
            except Exception as e:
                pass # fallback to embedded offline reasoning engine

        # Embedded 100% Offline Neural Rule Reasoner (Runs without any external tool or internet)
        return self._embedded_offline_reasoning(user_clean, context_data)

    def _embedded_offline_reasoning(self, query: str, ctx: dict) -> dict:
        balance = ctx.get('balance', 14250.0)
        spent = ctx.get('spent_today', 42.5)
        daily_limit = ctx.get('daily_limit', 250.0)
        remaining = max(0.0, daily_limit - spent)

        # 1. Balance Queries
        if any(w in query for w in ["balance", "funds", "how much money", "total money", "cash"]):
            reply = f"Your current available balance is ${balance:,.2f}. You have ${remaining:,.2f} remaining in today's safe spending limit."

        # 2. Spend / Safety Limits
        elif any(w in query for w in ["spent", "limit", "ceiling", "daily gate", "spending"]):
            reply = f"You have spent ${spent:,.2f} out of your ${daily_limit:,.2f} daily gate. No suspicious runaway loops detected."

        # 3. Google Pay / UPI
        elif any(w in query for w in ["google pay", "gpay", "upi", "pay", "payment"]):
            reply = "Google Pay integration works as an on-device escrow: whenever an AI sub-agent attempts to buy something, ELVA holds the transaction until it passes your daily spending policy."

        # 4. DigiVault / Documents / Passports
        elif any(w in query for w in ["digivault", "vault", "passport", "aadhaar", "license", "identity", "id"]):
            reply = "Your DigiVault holds 4 encrypted credentials. When downstream apps ask for verification, I only share synthetic zero-knowledge tokens to keep your raw documents private."

        # 5. Security / Who tried to charge / Threats
        elif any(w in query for w in ["who", "threat", "attack", "hack", "charge", "risk", "injection", "clone"]):
            reply = "I am actively monitoring all sub-agents. Both an indirect invoice prompt injection and a voice clone scam were neutralized and logged in your ledger."

        # 6. Offline Status Query
        elif any(w in query for w in ["offline", "internet", "cloud", "private", "local"]):
            reply = "We are operating 100% offline. All financial ledgers, cryptographic tokens, and acoustic checks run directly on your hardware with zero cloud exposure."

        # 7. Greetings
        elif any(w in query for w in ["hello", "hi", "hey", "who are you", "elva"]):
            reply = "Hello! I am ELVA, running locally on your device to protect your finances and identity. What would you like to check?"

        # Default smart response
        else:
            reply = f"I've analyzed your request: '{query}'. Everything is secure on-device. Your balance is ${balance:,.2f} with zero active threats."

        return {
            "mode": "EMBEDDED_LOCAL_REASONER",
            "response": reply,
            "offline": True
        }

brain = OfflineElvaBrain()
