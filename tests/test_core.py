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


if __name__ == "__main__":
    unittest.main()
