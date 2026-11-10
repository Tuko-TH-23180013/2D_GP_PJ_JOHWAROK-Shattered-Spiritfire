import unittest

from player import Player
from weapon_data import WEAPONS
from world import World, Rect


class WeaponTests(unittest.TestCase):
    def test_switch_invulnerability_has_own_timer(self):
        p = Player(y=1000)
        p.start_dash()
        p.request_switch()
        self.assertFalse(p.dash_invulnerable)
        self.assertTrue(p.invulnerable)
        p.end_dash_invulnerability()
        self.assertTrue(p.invulnerable)
        p.update(0.11, 0, False, World([]))
        self.assertFalse(p.invulnerable)
        self.assertGreater(p.switch_remaining, 0)

    def test_switch_in_hazard_then_vulnerable_tail(self):
        p = Player(y=1000)
        world = World([])
        world.hazards = [Rect(-1000, -1000, 20000, 20000)]
        p.request_switch()
        p.update(0.05, 0, False, world)
        self.assertEqual(p.hazard_hits, 0)
        p.request_switch()  # 연속 입력이 무적을 연장하지 않는다.
        p.update(0.07, 0, False, world)
        self.assertEqual(p.hazard_hits, 1)
        self.assertFalse(p.invulnerable)

    def test_new_dash_does_not_erase_switch_invulnerability(self):
        p = Player(y=1000)
        p.request_switch()
        p.start_dash()
        p.update(0.09, 0, False, World([]))
        self.assertFalse(p.dash_invulnerable)
        self.assertTrue(p.invulnerable)

    def test_giant_damage_after_game_switch(self):
        import sdl2
        from main import Game
        for fps in (20, 60, 144):
            game = Game()
            game.player.x = 350
            game.inputs.pressed = {sdl2.SDLK_SPACE}
            game.update(1 / fps)
            game.inputs.pressed.clear()
            for _ in range(fps // 2):
                game.update(1 / fps)
            game.inputs.pressed = {sdl2.SDLK_x}
            game.update(1 / fps)
            game.inputs.pressed.clear()
            for _ in range(fps):
                game.update(1 / fps)
            self.assertEqual(game.dummy.hp, 176)
            self.assertIsNone(game.player.attack)

    def test_switch_resets_combo_and_blocks_repeat(self):
        p = Player()
        self.assertTrue(p.request_switch())
        self.assertEqual(p.weapon, 'giant')
        self.assertFalse(p.request_switch())
        p.request_attack()
        self.assertIsNone(p.attack)
        p.update(0.2, 0, False, World([]))
        p.grounded = True
        p.request_attack()
        self.assertEqual(p.attack.combo_index, 0)
        self.assertIs(p.attack.data, WEAPONS['giant'].combo[0])

    def test_queued_switch_executes_once_before_combo(self):
        p = Player()
        p.grounded = True
        p.request_attack()
        original = p.attack
        p.request_attack()
        p.request_switch()
        p.request_switch()
        self.assertIs(p.attack, original)
        self.assertEqual(p.weapon, 'basic')
        p.advance_attack(1)
        self.assertEqual(p.weapon, 'giant')
        self.assertFalse(p.switch_queued)
        self.assertFalse(p.attack_queued)
        self.assertIsNone(p.attack)
        p.update(0.5, 0, False, World([]))
        self.assertEqual(p.weapon, 'giant')

    def test_dash_cancel_resolves_pending_switch(self):
        p = Player()
        p.grounded = True
        p.request_attack()
        p.request_switch()
        self.assertFalse(p.start_dash())
        p.attack.advance(0.21)
        self.assertTrue(p.start_dash())
        self.assertEqual(p.weapon, 'giant')
        self.assertIsNone(p.attack)
        self.assertGreater(p.dash_remaining, 0)
        self.assertFalse(p.dash_invulnerable)

    def test_switch_during_dash_keeps_movement(self):
        p = Player()
        p.start_dash()
        p.request_switch()
        self.assertGreater(p.dash_remaining, 0)
        self.assertFalse(p.dash_invulnerable)
        self.assertEqual(p.weapon, 'giant')

    def test_game_space_and_reset_clear_pending(self):
        from main import Game
        import sdl2
        game = Game()
        game.inputs.pressed = {sdl2.SDLK_SPACE, sdl2.SDLK_x}
        game.update(0.02)
        self.assertEqual(game.player.weapon, 'giant')
        self.assertIsNone(game.player.attack)
        game.player.switch_queued = True
        game.inputs.pressed = {sdl2.SDLK_r}
        game.update(0.02)
        self.assertFalse(game.player.switch_queued)

    def test_giant_two_hit_combo(self):
        p = Player(weapon="giant")
        p.grounded = True
        p.request_attack()
        first = p.attack
        p.request_attack()
        p.advance_attack(1)
        self.assertEqual(p.attack.combo_index, 1)
        self.assertIsNot(p.attack, first)
        p.request_attack()
        p.advance_attack(1)
        self.assertEqual(p.attack.combo_index, 0)

    def test_giant_slower_wider_stronger(self):
        basic = WEAPONS['basic'].combo[0]
        giant = WEAPONS['giant'].combo[0]
        self.assertGreater(giant.startup, basic.startup)
        self.assertGreater(giant.reach, basic.reach)
        self.assertGreater(giant.damage, basic.damage)
        p = Player(weapon="giant")
        p.request_attack()
        self.assertIs(p.attack.data, WEAPONS['giant'].air)


if __name__ == '__main__':
    unittest.main()
