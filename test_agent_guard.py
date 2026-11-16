import os
import tempfile
import unittest

from agent_guard import Guard, Policy


def make_guard():
    tmp = tempfile.mkdtemp()
    policy = Policy(max_per_payment=50.0, daily_limit=100.0, allowed_merchants={"CableShop", "AudioHaus"})
    return Guard(policy, os.path.join(tmp, "audit_log.jsonl"))


def no(merchant, amount, note):
    return False


def yes(merchant, amount, note):
    return True


class GuardRules(unittest.TestCase):
    def test_allows_small_payment_to_allowed_merchant(self):
        g = make_guard()
        d = g.request_payment("a", "CableShop", 19.0, "cable", no)
        self.assertEqual(d.status, "allowed")
        self.assertEqual(g.spent_today, 19.0)

    def test_blocks_unknown_merchant(self):
        g = make_guard()
        d = g.request_payment("a", "quick-deals.shop", 5.0, "gift card", yes)
        self.assertEqual(d.status, "blocked")
        self.assertEqual(g.spent_today, 0.0)

    def test_human_no_denies_payment_above_cap(self):
        g = make_guard()
        d = g.request_payment("a", "AudioHaus", 60.0, "headphones", no)
        self.assertEqual(d.status, "denied_by_human")
        self.assertEqual(g.spent_today, 0.0)

    def test_human_yes_allows_payment_above_cap_within_daily_limit(self):
        g = make_guard()
        d = g.request_payment("a", "AudioHaus", 60.0, "headphones", yes)
        self.assertEqual(d.status, "allowed")
        self.assertEqual(g.spent_today, 60.0)

    def test_daily_limit_cannot_be_overridden_by_human(self):
        g = make_guard()
        g.request_payment("a", "CableShop", 19.0, "cable", no)
        d = g.request_payment("a", "AudioHaus", 240.0, "headphones", yes)
        self.assertEqual(d.status, "blocked")
        self.assertEqual(g.spent_today, 19.0)

    def test_daily_limit_blocks_small_payments_too(self):
        g = make_guard()
        g.request_payment("a", "CableShop", 45.0, "brick", no)
        g.request_payment("a", "CableShop", 45.0, "brick", no)
        d = g.request_payment("a", "CableShop", 45.0, "brick", no)
        self.assertEqual(d.status, "blocked")
        self.assertEqual(g.spent_today, 90.0)

    def test_human_is_asked_only_above_cap(self):
        g = make_guard()
        asked = []

        def spy(merchant, amount, note):
            asked.append(amount)
            return False

        g.request_payment("a", "CableShop", 50.0, "at cap", spy)
        g.request_payment("a", "CableShop", 50.01, "just above cap", spy)
        self.assertEqual(asked, [50.01])

    def test_every_attempt_is_logged(self):
        g = make_guard()
        g.request_payment("a", "CableShop", 19.0, "cable", no)
        g.request_payment("a", "nowhere.shop", 5.0, "x", no)
        g.request_payment("a", "AudioHaus", 240.0, "headphones", no)
        log = g.read_log()
        self.assertEqual([r["decision"] for r in log], ["allowed", "blocked", "denied_by_human"])


if __name__ == "__main__":
    unittest.main()
