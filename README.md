# agent-guard

A small spending guard that sits between an AI agent and a payment call.

**Test payments only. No network, no real money, no real AI model.** The demo agent is a scripted simulation.

## Run the demo

```
python3 demo.py
```

Python 3.8+ and nothing else. The guard asks you once: type `n` (or just press Enter) to refuse the $240 purchase.

## What the guard does

Rules, checked in this order:

1. Merchant not on the allowlist: blocked.
2. Single payment above the per-payment cap ($50 in the demo): the guard asks a human. Default answer is no.
3. Today's total would pass the daily cap ($100 in the demo): blocked. A human "yes" cannot override this.
4. Otherwise: allowed.

Every attempt, allowed or not, is written to `audit_log.jsonl`.

## Use it in your own code

```python
from agent_guard import Guard, Policy

guard = Guard(Policy(max_per_payment=50, daily_limit=100, allowed_merchants={"CableShop"}))
decision = guard.request_payment("my-agent", "CableShop", 19.0, "USB-C cable",
                                 ask_human=lambda m, a, n: False)
print(decision.status, decision.reason)
```

Put the real payment call behind `decision.status == "allowed"`.

## Limits

This is a demo of the idea. It does not connect to ChatGPT Wallet or any real payment provider, and it does not stop an agent from finding another way to pay. Treat it as a pattern to build on.
