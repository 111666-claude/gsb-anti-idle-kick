import random
import unittest

from idle.core import IdleGuard


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

    def test_whitelist_always_ok(self):
        guard = IdleGuard(1000, 500)
        guard.allow("p")
        guard.touch("e1", "p", 0)
        self.assertEqual(guard.check("p", 1000), "ok")
        self.assertEqual(guard.check("p", 1500), "ok")
        self.assertEqual(guard.check("p", 999999), "ok")

    def test_whitelist_without_touch_is_ok(self):
        guard = IdleGuard(1000, 500)
        guard.allow("p")
        self.assertEqual(guard.check("p", 999999), "ok")

    def test_exact_idle_boundary_times_out(self):
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        self.assertEqual(guard.check("p", 1000), "warn")

    def test_exact_kick_boundary(self):
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        self.assertEqual(guard.check("p", 1500), "warn")
        self.assertEqual(guard.check("p", 1501), "kick")

    def test_grace_window_warns(self):
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        for now_ms in (1000, 1001, 1200, 1499, 1500):
            self.assertEqual(guard.check("p", now_ms), "warn")

    def test_touch_during_grace_resets_to_ok(self):
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        self.assertEqual(guard.check("p", 1200), "warn")
        guard.touch("e2", "p", 1200)
        self.assertEqual(guard.check("p", 1200), "ok")
        self.assertEqual(guard.check("p", 2200), "warn")
        self.assertEqual(guard.check("p", 2701), "kick")

    def test_duplicate_event_id_is_idempotent(self):
        guard = IdleGuard(1000, 500)
        guard.touch("e1", "p", 0)
        guard.touch("e1", "p", 2000)
        self.assertEqual(guard.check("p", 1000), "warn")
        guard.touch("e1", "p", 2000)
        self.assertEqual(guard.check("p", 1501), "kick")

    def test_repeated_sequence_is_stable(self):
        def run():
            guard = IdleGuard(1000, 500)
            guard.allow("w")
            results = []
            for event_id, player, now_ms in [
                ("e1", "p", 0), ("e2", "w", 0), ("e1", "p", 500),
            ]:
                guard.touch(event_id, player, now_ms)
            for player, now_ms in [
                ("p", 1000), ("p", 1500), ("w", 9999), ("p", 1501),
                ("ghost", 1),
            ]:
                results.append(guard.check(player, now_ms))
            return results
        self.assertEqual(run(), run())

    def test_scanned_count_is_check_count(self):
        guard = IdleGuard(1000, 500)
        for index in range(3000):
            guard.touch("e-%d" % index, "p-%d" % index, 0)
        for _ in range(3000):
            guard.check("p-0", 0)
        self.assertLessEqual(guard.scanned_count(), 3000)

    def test_matches_reference_on_random_sequences(self):
        def reference(events, checks, whitelist, idle_ms, grace_ms):
            last = {}
            seen = set()
            out = []
            for event_id, player, now_ms in events:
                if event_id in seen:
                    continue
                seen.add(event_id)
                if player not in last or now_ms > last[player]:
                    last[player] = now_ms
            for player, now_ms in checks:
                if player in whitelist or player not in last:
                    out.append("ok")
                    continue
                idle = now_ms - last[player]
                if idle < idle_ms:
                    out.append("ok")
                elif idle <= idle_ms + grace_ms:
                    out.append("warn")
                else:
                    out.append("kick")
            return out

        rng = random.Random(20261004)
        for _ in range(200):
            idle_ms = rng.randint(1, 2000)
            grace_ms = rng.randint(0, 2000)
            guard = IdleGuard(idle_ms, grace_ms)
            players = ["p%d" % i for i in range(rng.randint(1, 8))]
            whitelist = set(rng.sample(players, rng.randint(0, len(players))))
            for player in whitelist:
                guard.allow(player)
            events = []
            event_seq = 0
            for _ in range(rng.randint(0, 30)):
                if rng.random() < 0.3 and events:
                    event_id = rng.choice(events)[0]
                else:
                    event_id = "e%d" % event_seq
                    event_seq += 1
                event = (event_id, rng.choice(players), rng.randint(0, 5000))
                events.append(event)
                guard.touch(*event)
            checks = []
            candidates = players + ["ghost"]
            for _ in range(rng.randint(1, 30)):
                checks.append((rng.choice(candidates), rng.randint(0, 5000)))
            actual = [guard.check(player, now_ms) for player, now_ms in checks]
            expected = reference(events, checks, whitelist, idle_ms, grace_ms)
            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
