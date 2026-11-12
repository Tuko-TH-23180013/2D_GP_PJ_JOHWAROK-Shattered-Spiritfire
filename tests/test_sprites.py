import struct
import unittest
from player import Player
from sprite_animation import ASSET_ROOT, HeroAnimation, source_rect, draw_center, HERO_SCALE


class SpriteTests(unittest.TestCase):
    def test_restart_reuses_loaded_resources(self):
        from main import Game
        game = Game()
        resource = object()
        game.visuals = resource
        game.restart()
        self.assertIs(game.visuals, resource)
        self.assertEqual(game.hero_animation.frame, 0)

    def test_game_attack_and_debug_key(self):
        import sdl2
        from main import Game
        game = Game()
        game.inputs.pressed = {sdl2.SDLK_x, sdl2.SDLK_F2}
        game.update(1 / 60)
        self.assertEqual(game.hero_animation.frame, 10)
        self.assertTrue(game.show_hitboxes)

    def test_sheet_dimensions_and_crop_coordinates(self):
        raw = (ASSET_ROOT / 'hero.png').read_bytes()
        self.assertEqual(raw[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>II', raw[16:24]), (800, 800))
        self.assertEqual(source_rect(0), (0, 640, 160, 160))
        self.assertEqual(source_rect(24), (640, 0, 160, 160))
        with self.assertRaises(ValueError):
            source_rect(25)

    def test_foot_anchor_and_camera(self):
        p = Player(900, 235)
        x, y = draw_center(p, 500)
        self.assertEqual(x, 418)
        self.assertAlmostEqual(y - 53 * HERO_SCALE, p.y)

    def test_attack_frames_follow_phase_and_keep_air_type(self):
        p, anim = Player(), HeroAnimation()
        for weapon, combos in [('basic', [(10, 11, 12), (13, 14, 15), (16, 17, 18)]),
                               ('giant', [(22, 23, 24), (16, 23, 18)])]:
            p.weapon = weapon
            for index, frames in enumerate(combos):
                p.grounded = True
                p.start_attack(index)
                for elapsed, expected in zip((0, p.attack.data.startup,
                                             p.attack.data.startup + p.attack.data.active), frames):
                    p.attack.elapsed = elapsed
                    anim.update(p, 0.01, p.x)
                    self.assertEqual(anim.frame, expected)
        p.grounded = False
        p.start_attack()
        p.grounded = True
        anim.update(p, 0.01, p.x)
        self.assertEqual(anim.frame, 19)

    def test_motion_frames_and_no_state_mutation(self):
        p, anim = Player(), HeroAnimation()
        p.grounded = True
        before = dict(vars(p))
        anim.update(p, 0.1, p.x - 3)
        self.assertIn(anim.frame, range(2, 6))
        self.assertEqual(vars(p), before)
        p.grounded = False
        for vy, frame in [(200, 6), (0, 7), (-200, 8)]:
            p.vy = vy
            anim.update(p, 0.1, p.x)
            self.assertEqual(anim.frame, frame)
        p.start_dash()
        anim.update(p, 0.01, p.x)
        self.assertEqual(anim.frame, 9)
