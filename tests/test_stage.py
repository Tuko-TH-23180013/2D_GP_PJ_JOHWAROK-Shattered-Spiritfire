import unittest
from stage import VillageStage
from player import Player
from camera import Camera


class StageTests(unittest.TestCase):
    def test_camera_clamp_and_world_coordinates(self):
        p = Player()
        camera = Camera(3200)
        camera.follow(p)
        self.assertEqual(camera.x, 0)
        p.x = 1600
        camera.follow(p)
        self.assertAlmostEqual(camera.screen_rect(p.x, p.y, p.x + p.width, p.y + p.height)[0], 622)
        self.assertEqual(p.x, 1600)
        p.x = 3100
        camera.follow(p)
        self.assertEqual(camera.x, 1920)
        small = Camera(500)
        small.follow(p)
        self.assertEqual(small.x, 0)

    def test_scrolled_combat_uses_world_coordinates(self):
        from main import Game
        from enemy import Enemy
        import sdl2
        game = Game()
        game.player.x = 1700
        game.enemies = [Enemy(1780)]
        game.enemies[0].hp = 10
        game.inputs.pressed = {sdl2.SDLK_x}
        game.update(0.05)
        game.inputs.pressed.clear()
        for _ in range(10):
            game.update(0.05)
        self.assertGreater(game.camera.x, 0)
        self.assertEqual(game.enemies, [])
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
