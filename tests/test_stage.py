import unittest
from stage import VillageStage
from player import Player


class StageTests(unittest.TestCase):
    def test_spawn_and_right_boundary(self):
        stage = VillageStage()
        p = Player(*stage.spawn)
        world = stage.create_world()
        p.update(0.05, 0, False, world)
        self.assertTrue(p.grounded)
        p.x = stage.width - p.width
        p.update(0.05, 1, False, world)
        self.assertEqual(p.x + p.width, stage.width)

    def test_move_and_double_jump_route_reaches_gate(self):
        stage = VillageStage()
        world = stage.create_world()
        p = Player(*stage.spawn)
        jumped = False
        air_frames = 0
        for _ in range(1800):
            jump = False
            if not jumped and p.x >= 970:
                jump = True
                jumped = True
            if jumped:
                air_frames += 1
                if air_frames == 18:
                    jump = True
            p.update(1 / 60, 1, jump, world)
            if p.x >= stage.boss_entrance.left:
                break
        self.assertGreaterEqual(p.x, stage.boss_entrance.left)
        self.assertEqual(stage.region_at(p.x), 'Boss gate')
