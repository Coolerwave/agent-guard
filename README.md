# agent-guard

A small spending guard that sits between an AI agent and a payment call.

**Test payments only. No network, no real money, no real AI model.** The demo agent is a scripted simulation.

AI agents are starting to get wallets. This repo shows one simple pattern for keeping them on a leash: limits, a human check for big payments, and a log of everything.

## Run the demo

```
python3 demo.py
```

Python 3.8+ and nothing else. When the guard asks `[y/N]`, type `n` (or press Enter) to refuse the $240 purchase.

Sample run:

```
agent> buying USB-C cable ($19.00) from CableShop
  ALLOWED  within limits

agent> buying noise-cancelling headphones ($240.00) from AudioHaus
  ? GUARD asks you: approve $240.00 to AudioHaus?
    [y/N] n
  DENIED   amount above $50.00 cap, human said no

agent> buying gift card ($35.00) from quick-deals.shop
  BLOCKED  merchant is not on the allowlist

agent> buying charging brick ($45.00) from CableShop
  ALLOWED  within limits

agent> buying second charging brick ($45.00) from CableShop
  BLOCKED  daily limit $100.00 would be passed (spent $64.00)

Agent tried to spend $384.00. Guard let through $64.00 and stopped $320.00.
```

## What the guard does

Rules, checked in this order:

| # | Rule | Result |
|---|------|--------|
| 1 | Merchant is not on the allowlist | Blocked, no override |
| 2 | Single payment above the per-payment cap ($50 in the demo) | Asks a human, default answer is no |
| 3 | Today's total would pass the daily cap ($100 in the demo) | Blocked, a human "yes" cannot override it |
| 4 | Otherwise | Allowed |

Every attempt, allowed or not, is written to `audit_log.jsonl`.

## Use it in your own code

```python
from agent_guard import Guard, Policy

guard = Guard(Policy(max_per_payment=50, daily_limit=100, allowed_merchants={"CableShop"}))
decision = guard.request_payment("my-agent", "CableShop", 19.0, "USB-C cable",
                                 ask_human=lambda merchant, amount, note: False)
print(decision.status, decision.reason)
```

Put the real payment call behind `decision.status == "allowed"`.

## Tests

```
python3 -m unittest -v
```

## Limits

This is a demo of the idea. It does not connect to ChatGPT Wallet or any real payment provider, and it does not stop an agent from finding another way to pay. The daily total lives in memory and resets when the process restarts. Treat it as a pattern to build on, not as a security product.

## License

MIT
