import unittest

from player import Player
from settings import MAX_FALL_SPEED
from world import Rect, World


class MovementTests(unittest.TestCase):
    def setUp(self):
        self.world = World([Rect(-1000, 0, 3000, 100)])
        self.player = Player()

    def test_double_jump_third_press_and_landing_reset(self):
        p = self.player
        p.update(0.05, 0, True, self.world)
        self.assertEqual(p.jumps_used, 1)
        p.update(0.05, 0, True, self.world)
        self.assertEqual(p.jumps_used, 2)
        speed = p.vy
        p.update(0.05, 0, True, self.world)
        self.assertLess(p.vy, speed)
        for _ in range(60):
            p.update(0.05, 0, False, self.world)
        self.assertEqual(p.y, 100)
        self.assertEqual(p.jumps_used, 0)
        self.assertTrue(p.grounded)

    def test_frame_rates(self):
        results = []
        for fps in (20, 30, 60, 144):
            p = Player()
            peak = p.y
            for frame in range(fps):
                p.update(1 / fps, 1, frame == 0, self.world)
                peak = max(peak, p.y)
            results.append((p.x, peak))
        self.assertLess(max(x for x, _ in results) - min(x for x, _ in results), 0.01)
        self.assertLess(max(y for _, y in results) - min(y for _, y in results), 1.0)

    def test_wall_both_sides(self):
        world = World([Rect(200, 0, 220, 300)])
        p = Player(100, 120)
        world.move_x(p, 500)
        self.assertEqual(p.x + p.width, 200)
        p.x = 300
        world.move_x(p, -500)
        self.assertEqual(p.x, 220)

    def test_platform_top_and_underside(self):
        world = World([Rect(100, 210, 300, 235)])
        p = Player(150, 100)
        p.update(0.05, 0, True, world)
        p.update(0.05, 0, False, world)
        self.assertLessEqual(p.y + p.height, 210)
        self.assertLessEqual(p.vy, 0)
        p.y = 400
        p.vy = -MAX_FALL_SPEED
        for _ in range(10):
            p.update(0.05, 0, False, world)
        self.assertEqual(p.y, 235)
        self.assertTrue(p.grounded)

    def test_walk_off_allows_only_one_air_jump(self):
        world = World([Rect(0, 0, 150, 100)])
        p = Player(140, 100)
        p.update(0.05, 1, False, world)
        self.assertFalse(p.grounded)
        self.assertEqual(p.jumps_used, 1)
        p.update(0.05, 0, True, world)
        speed = p.vy
        p.update(0.05, 0, True, world)
        self.assertLess(p.vy, speed)

    def test_fall_speed_and_facing(self):
        p = Player(y=10000)
        for _ in range(100):
            p.update(0.05, -1, False, World([]))
        self.assertEqual(p.vy, -MAX_FALL_SPEED)
        self.assertEqual(p.facing, -1)
        p.update(0.05, 0, False, World([]))
        self.assertEqual(p.facing, -1)

    def test_drop_lands_on_next_platform(self):
        upper = Rect(100, 300, 300, 320, one_way=True)
        lower = Rect(100, 200, 300, 220, one_way=True)
        world = World([upper, lower, Rect(0, 0, 500, 100)])
        p = Player(150, 320)
        p.update(0.05, 0, True, world, down_held=True)
        self.assertLess(p.y, 320)
        self.assertLess(p.vy, 0)
        for _ in range(20):
            p.update(0.05, 0, False, world, down_held=True)
        self.assertEqual(p.y, 220)
        self.assertTrue(p.grounded)
        self.assertEqual(p.jumps_used, 0)

    def test_down_jump_on_floor_does_not_drop(self):
        p = self.player
        p.update(0.05, 0, True, self.world, down_held=True)
        self.assertGreater(p.y, 100)
        self.assertFalse(p.drop_platforms)

    def test_one_way_passes_up_then_lands(self):
        platform = Rect(100, 210, 300, 235, one_way=True)
        world = World([*self.world.solids, platform])
        p = Player(150, 100)
        peak = p.y
        for frame in range(60):
            p.update(1 / 60, 0, frame == 0 or frame == 10, world)
            peak = max(peak, p.y)
        self.assertGreater(peak, platform.top)
        self.assertEqual(p.y, platform.top)

    def test_drop_at_different_frame_rates(self):
        for fps in (20, 60, 144):
            world = World([Rect(0, 0, 500, 100),
                           Rect(100, 200, 300, 220, one_way=True)])
            p = Player(150, 220)
            for frame in range(fps):
                p.update(1 / fps, 0, frame == 0, world, down_held=True)
            self.assertEqual(p.y, 100)


if __name__ == '__main__':
    unittest.main()
