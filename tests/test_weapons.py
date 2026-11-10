import unittest

from player import Player
from weapon_data import WEAPONS
from world import World


class WeaponTests(unittest.TestCase):
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
