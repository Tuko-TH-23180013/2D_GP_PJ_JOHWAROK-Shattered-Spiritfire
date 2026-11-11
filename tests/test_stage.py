import unittest
from stage import VillageStage
from player import Player
from camera import Camera


class StageTests(unittest.TestCase):
    def test_checkpoint_requires_nearby_grounded_living_player(self):
        from checkpoint import Checkpoint
        cp = Checkpoint((2500, 100))
        p = Player()
        p.grounded = True
        self.assertFalse(cp.activate(p))
        p.x = 2500
        p.grounded = False
        self.assertFalse(cp.activate(p))
        p.grounded = True
        p.hp = 0
        self.assertFalse(cp.activate(p))
        p.hp = 100
        self.assertTrue(cp.activate(p))

    def test_checkpoint_restart_resets_combat_but_keeps_checkpoint(self):
        from main import Game
        import sdl2
        game = Game()
        game.player.x = 2500
        game.inputs.pressed = {sdl2.SDLK_UP}
        game.update(0.02)
        self.assertTrue(game.checkpoint.active)
        for _ in range(3):
            game.player.request_attack()
            game.player.request_switch()
            game.player.hp = 0
            game.enemies.clear()
            game.inputs.held = {sdl2.SDLK_RIGHT}
            game.inputs.pressed = {sdl2.SDLK_r, sdl2.SDLK_x}
            game.update(0.02)
            self.assertEqual((game.player.x, game.player.y, game.player.hp), (2500, 100, 100))
            self.assertTrue(game.checkpoint.active)
            self.assertEqual(game.player.dash_charges, 2)
            self.assertIsNone(game.player.attack)
            self.assertFalse(game.player.switch_queued)
            self.assertFalse(game.inputs.held or game.inputs.pressed)
            self.assertEqual(len(game.enemies), 1)
            self.assertGreater(game.camera.x, 0)

    def test_playable_route_checkpoint_and_gate(self):
        from main import Game
        import sdl2
        game = Game()
        game.inputs.held = {sdl2.SDLK_RIGHT}
        jumped = False
        air_frames = 0
        for frame in range(1800):
            keys = set()
            if frame % 12 == 0:
                keys.add(sdl2.SDLK_x)
            if not jumped and game.player.x >= 970:
                jumped = True
                keys.add(sdl2.SDLK_c)
            if jumped:
                air_frames += 1
                if air_frames == 18:
                    keys.add(sdl2.SDLK_c)
            if 2460 < game.player.x < 2520:
                keys.add(sdl2.SDLK_UP)
            game.inputs.pressed = keys
            game.update(1 / 60)
            if game.at_boss_gate:
                break
        self.assertGreater(game.player.hp, 0)
        self.assertTrue(game.checkpoint.active)
        self.assertTrue(game.at_boss_gate)
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
