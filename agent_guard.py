"""agent_guard: a small spending guard that sits between an AI agent and a payment call.

Rules, checked in this order:
  1. Merchant not on the allowlist            -> BLOCK (no override)
  2. Single payment above the per-payment cap -> ASK a human (default answer: no)
  3. Today's total would pass the daily cap   -> BLOCK (a human "yes" cannot override this)
  4. Otherwise                                -> ALLOW

Every attempt, allowed or not, is written to a JSON lines audit log.
Standard library only. This module never moves real money.
"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Policy:
    max_per_payment: float = 50.0
    daily_limit: float = 100.0
    allowed_merchants: set = field(default_factory=set)


@dataclass
class Decision:
    status: str  # "allowed", "blocked" or "denied_by_human"
    reason: str


class Guard:
    def __init__(self, policy, log_path="audit_log.jsonl"):
        self.policy = policy
        self.log_path = Path(log_path)
        self.spent_today = 0.0

    def request_payment(self, agent, merchant, amount, note, ask_human):
        """ask_human(merchant, amount, note) -> bool. Called only for rule 2."""
        p = self.policy
        asked_human = False
        approved = False
        if merchant not in p.allowed_merchants:
            d = Decision("blocked", "merchant is not on the allowlist")
        else:
            if amount > p.max_per_payment:
                asked_human = True
                approved = bool(ask_human(merchant, amount, note))
            if asked_human and not approved:
                d = Decision("denied_by_human", "amount above $%.2f cap, human said no" % p.max_per_payment)
            elif self.spent_today + amount > p.daily_limit:
                d = Decision(
                    "blocked",
                    "daily limit $%.2f would be passed (spent $%.2f)"
                    % (p.daily_limit, self.spent_today),
                )
            elif asked_human:
                d = Decision("allowed", "approved by human above $%.2f cap" % p.max_per_payment)
            else:
                d = Decision("allowed", "within limits")

        if d.status == "allowed":
            self.spent_today += amount
        self._log(agent, merchant, amount, note, d)
        return d

    def _log(self, agent, merchant, amount, note, d):
        row = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "agent": agent,
            "merchant": merchant,
            "amount": amount,
            "note": note,
            "decision": d.status,
            "reason": d.reason,
        }
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def read_log(self):
        if not self.log_path.exists():
            return []
        with self.log_path.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
