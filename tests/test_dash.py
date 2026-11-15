import unittest

from player import Player
from world import World, Rect
from settings import DASH_SPEED, DASH_DURATION


class DashTests(unittest.TestCase):
    def test_horizontal_dash_freezes_height_and_gravity(self):
        for fps in (20, 60, 144):
            for vy in (-500, 400):
                p = Player(y=500)
                p.vy = vy
                start_x = p.x
                p.start_dash()
                remaining = DASH_DURATION
                while remaining > 1e-9:
                    step = min(1 / fps, remaining)
                    p.update(step, 0, False, World([]))
                    remaining -= step
                    self.assertEqual(p.y, 500)
                    self.assertEqual(p.vy, vy)
                self.assertAlmostEqual(p.x - start_x, DASH_SPEED * DASH_DURATION)
                p.update(.01, 0, False, World([]))
                self.assertLess(p.vy, vy)
                self.assertNotEqual(p.y, 500)

    def setUp(self):
        self.p = Player(y=10000)
        self.world = World([])

    def advance(self, seconds):
        while seconds > 1e-9:
            step = min(seconds, 0.01)
            self.p.update(step, 0, False, self.world)
            seconds -= step

    def test_two_charges_and_sequential_air_recharge(self):
        self.assertTrue(self.p.start_dash())
        self.advance(0.28)
        self.assertTrue(self.p.start_dash())
        self.advance(0.28)
        self.assertFalse(self.p.start_dash())
        self.assertEqual(self.p.dash_charges, 0)
        self.advance(0.44)
        self.assertEqual(self.p.dash_charges, 1)
        self.advance(1)
        self.assertEqual(self.p.dash_charges, 2)

    def test_invulnerability_tail_and_gap(self):
        self.p.start_dash()
        self.advance(0.04)
        self.assertTrue(self.p.dash_invulnerable)
        self.advance(0.05)
        self.assertFalse(self.p.dash_invulnerable)
        self.assertGreater(self.p.dash_remaining, 0)
        self.advance(0.12)
        self.assertFalse(self.p.start_dash())
        self.advance(0.07)
        self.assertTrue(self.p.start_dash())

    def test_successful_jump_ends_only_invulnerability(self):
        self.p.start_dash()
        old_x = self.p.x
        self.p.update(0.02, 0, True, self.world)
        self.assertFalse(self.p.dash_invulnerable)
        self.assertGreater(self.p.dash_remaining, 0)
        self.assertAlmostEqual(self.p.x - old_x, DASH_SPEED * 0.02)
        self.assertGreater(self.p.vy, 0)

    def test_failed_jump_preserves_invulnerability(self):
        self.p.jumps_used = 2
        self.p.start_dash()
        self.p.update(0.02, 0, True, self.world)
        self.assertTrue(self.p.dash_invulnerable)

    def test_distance_frame_rates_and_wall(self):
        for fps in (20, 30, 60, 144):
            p = Player(y=10000)
            start = p.x
            p.start_dash()
            for _ in range(fps):
                p.update(1 / fps, 0, False, self.world)
            self.assertAlmostEqual(p.x - start, DASH_SPEED * DASH_DURATION)
        world = World([Rect(200, 0, 220, 200)])
        p = Player(120, 100)
        p.update(0.05, 1, False, world, dash_pressed=True)
        p.update(0.05, 1, False, world)
        self.assertEqual(p.x + p.width, 200)

    def test_hazard_invulnerability_then_exposure(self):
        self.world.hazards = [Rect(-1000, -1000, 20000, 20000)]
        self.p.start_dash()
        self.advance(0.04)
        self.assertEqual(self.p.hazard_hits, 0)
        self.advance(0.06)
        self.assertEqual(self.p.hazard_hits, 1)
        self.assertTrue(self.p.hazard_exposed)


if __name__ == '__main__':
    unittest.main()
