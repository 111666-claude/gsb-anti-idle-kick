import random
import unittest

from idle.core import IdleGuard


def reference_check(last, whitelist, player, now_ms, idle_ms, grace_ms):
    """独立参考实现：白名单覆盖 + 到点（含等于）+ 宽限窗口。"""
    if player in whitelist:
        return "ok"
    if player not in last:
        return "ok"
    elapsed = now_ms - last[player]
    if elapsed < idle_ms:
        return "ok"
    if elapsed <= idle_ms + grace_ms:
        return "warn"
    return "kick"


class IdleTest(unittest.TestCase):
    def test_fresh_player_is_ok(self):
        self.assertEqual(IdleGuard(1000, 500).check("p", 0), "ok")

    def test_recent_touch_is_ok(self):
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        self.assertEqual(guard.check("p", 100), "ok")

    def test_long_idle_kicks(self):
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        self.assertEqual(guard.check("p", 5000), "kick")

    def test_scanned_starts_at_zero(self):
        self.assertEqual(IdleGuard(1000, 500).scanned_count(), 0)

    def test_whitelisted_player_is_always_ok(self):
        guard = IdleGuard(1000, 500)
        guard.allow("p")
        guard.touch("e1", "p", 0)
        self.assertEqual(guard.check("p", 5000), "ok")
        self.assertEqual(guard.check("p", 10 ** 9), "ok")

    def test_whitelisted_player_without_record_is_ok(self):
        guard = IdleGuard(1000, 500)
        guard.allow("p")
        self.assertEqual(guard.check("p", 10 ** 9), "ok")

    def test_exact_idle_boundary_warns(self):
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        self.assertEqual(guard.check("p", 1000), "warn")

    def test_grace_window_warns_and_end_boundary_still_warns(self):
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        self.assertEqual(guard.check("p", 1001), "warn")
        self.assertEqual(guard.check("p", 1500), "warn")
        self.assertEqual(guard.check("p", 1501), "kick")

    def test_touch_inside_grace_resets_to_ok(self):
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        self.assertEqual(guard.check("p", 1400), "warn")
        guard.touch("e2", "p", 1400)
        self.assertEqual(guard.check("p", 1500), "ok")

    def test_duplicate_event_id_is_ignored(self):
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        guard.touch("e1", "p", 900)
        self.assertEqual(guard.check("p", 1000), "warn")
        self.assertEqual(guard.check("p", 1501), "kick")

    def test_replaying_same_sequence_is_deterministic(self):
        events = [("e%d" % i, "p%d" % (i % 3), i * 100) for i in range(10)]

        def run():
            guard = IdleGuard(1000, 500)
            guard.allow("p1")
            results = []
            for event_id, player, now_ms in events:
                guard.touch(event_id, player, now_ms)
                results.append(guard.check(player, now_ms))
            return results

        self.assertEqual(run(), run())

    def test_scanned_count_does_not_grow_with_checks(self):
        guard = IdleGuard(1000, 500)
        for index in range(3000):
            guard.touch("e-%d" % index, "p-%d" % index, 0)
        for _ in range(3000):
            guard.check("p-0", 0)
        self.assertLessEqual(guard.scanned_count(), 3000)

    def test_random_sequences_match_reference(self):
        rng = random.Random(20261004)
        for _ in range(200):
            idle_ms = rng.randint(1, 2000)
            grace_ms = rng.randint(0, 2000)
            guard = IdleGuard(idle_ms, grace_ms)
            last = {}
            whitelist = set()
            handled = set()
            players = ["p%d" % i for i in range(rng.randint(1, 5))]
            for player in players:
                if rng.random() < 0.3:
                    guard.allow(player)
                    whitelist.add(player)
            now = 0
            for _ in range(rng.randint(1, 60)):
                now += rng.randint(0, 3000)
                player = rng.choice(players)
                if rng.random() < 0.5:
                    event_id = "e%d" % rng.randint(0, 30)
                    if event_id not in handled:
                        handled.add(event_id)
                        last[player] = now
                    guard.touch(event_id, player, now)
                expected = reference_check(last, whitelist, player, now, idle_ms, grace_ms)
                self.assertEqual(guard.check(player, now), expected)


if __name__ == "__main__":
    unittest.main()
