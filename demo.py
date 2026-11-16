"""Demo: a SIMULATED shopping agent tries five purchases. The guard decides.

Test payments only. No network, no real money, no real AI model.
Run:   python3 demo.py
Flags: --fast       no pauses (for testing)
       --auto-deny  answer "no" to the human prompt automatically
"""
import os
import sys
import time

from agent_guard import Guard, Policy

FAST = "--fast" in sys.argv
AUTO_DENY = "--auto-deny" in sys.argv

USE_COLOR = sys.stdout.isatty() or os.environ.get("FORCE_COLOR")


def c(code, text):
    return "\033[%sm%s\033[0m" % (code, text) if USE_COLOR else text


def pause(s):
    if not FAST:
        time.sleep(s)


def ask_human(merchant, amount, note):
    print(c("33;1", "  ? GUARD asks you: approve $%.2f to %s?" % (amount, merchant)))
    if AUTO_DENY:
        print("    [y/N] n (auto)")
        return False
    try:
        answer = input("    [y/N] ").strip().lower()
    except EOFError:
        answer = "n"
    return answer == "y"


def main():
    log_path = "audit_log.jsonl"
    if os.path.exists(log_path):
        os.remove(log_path)

    policy = Policy(
        max_per_payment=50.0,
        daily_limit=100.0,
        allowed_merchants={"CableShop", "AudioHaus"},
    )
    guard = Guard(policy, log_path)

    print(c("1", "AGENT GUARD DEMO"))
    print(c("36", "SIMULATED AGENT  |  TEST PAYMENTS  |  NO REAL MONEY"))
    print("Rules: max $%.0f per payment, $%.0f per day, merchants: %s"
          % (policy.max_per_payment, policy.daily_limit, ", ".join(sorted(policy.allowed_merchants))))
    print()
    pause(1.5)

    attempts = [
        ("CableShop", 19.00, "USB-C cable"),
        ("AudioHaus", 240.00, "noise-cancelling headphones"),
        ("quick-deals.shop", 35.00, "gift card"),
        ("CableShop", 45.00, "charging brick"),
        ("CableShop", 45.00, "second charging brick"),
    ]

    for merchant, amount, note in attempts:
        print(c("1", "agent> ") + "buying %s ($%.2f) from %s" % (note, amount, merchant))
        pause(0.9)
        d = guard.request_payment("shopper-1", merchant, amount, note, ask_human)
        if d.status == "allowed":
            print(c("32;1", "  ALLOWED  ") + d.reason)
        elif d.status == "denied_by_human":
            print(c("31;1", "  DENIED   ") + d.reason)
        else:
            print(c("31;1", "  BLOCKED  ") + d.reason)
        print()
        pause(1.1)

    log = guard.read_log()
    tried = sum(r["amount"] for r in log)
    allowed = sum(r["amount"] for r in log if r["decision"] == "allowed")
    stopped = tried - allowed
    print(c("1", "AUDIT LOG (%s)" % log_path))
    for r in log:
        print("  %-16s $%-7.2f %-17s %s" % (r["decision"].upper(), r["amount"], r["merchant"], r["note"]))
    print()
    print("Agent tried to spend $%.2f. Guard let through $%.2f and stopped $%.2f."
          % (tried, allowed, stopped))


if __name__ == "__main__":
    main()
