import unittest

from attack import Attack, BASIC_COMBO
from combat_system import CombatSystem
from player import Player
from training_dummy import TrainingDummy
from world import World, Rect


class CombatTests(unittest.TestCase):
    def setUp(self):
        self.player = Player(350, 100)
        self.target = TrainingDummy()
        self.attack = Attack(self.player, BASIC_COMBO[0])
        self.combat = CombatSystem()

    def resolve(self, attacks=None):
        self.combat.resolve(attacks or [self.attack], [self.target])

    def test_only_active_and_once_per_attack(self):
        self.resolve()
        self.assertEqual(self.target.hp, 200)
        self.attack.advance(0.10)
        self.resolve()
        self.assertEqual(self.target.hp, 190)
        self.combat.begin_frame()
        self.resolve()
        self.assertEqual(self.target.hp, 190)
        self.attack.advance(0.10)
        self.target = TrainingDummy()
        self.resolve()
        self.assertEqual(self.target.hp, 200)

    def test_multiple_attacks_one_damage_per_frame(self):
        other = Attack(self.player, BASIC_COMBO[1])
        self.attack.advance(0.12)
        other.advance(0.12)
        self.resolve([self.attack, other])
        self.assertEqual(self.target.hp, 190)

    def test_invulnerability_and_miss(self):
        self.attack.advance(0.10)
        self.target.invulnerable = True
        self.resolve()
        self.assertEqual(self.target.hp, 200)
        self.target.invulnerable = False
        self.target.x = 900
        self.resolve()
        self.assertEqual(self.target.hp, 200)

    def test_stagger_reset(self):
        for _ in range(4):
            self.combat.begin_frame()
            attack = Attack(self.player, BASIC_COMBO[0])
            attack.advance(0.10)
            self.resolve([attack])
        self.assertGreater(self.target.stagger_remaining, 0)
        self.assertEqual(self.target.hp, 160)
        self.combat.update_target(self.target, 0.61)
        self.assertEqual(self.target.stagger, 0)

    def test_facing_is_captured(self):
        self.player.facing = -1
        self.assertEqual(self.attack.facing, 1)
        self.assertGreater(self.attack.bounds.right, self.player.x)

    def test_ground_combo_and_new_attack_objects(self):
        p = self.player
        p.grounded = True
        p.request_attack()
        attacks = [p.attack]
        for expected in (1, 2, 0):
            p.request_attack()
            p.advance_attack(1)
            self.assertEqual(p.attack.combo_index, expected)
            self.assertNotIn(p.attack, attacks)
            attacks.append(p.attack)

    def test_jump_and_landing_do_not_replace_attack(self):
        p = self.player
        world = World([Rect(0, 0, 1000, 100)])
        p.grounded = True
        p.request_attack()
        attack = p.attack
        p.update(0.02, -1, True, world)
        self.assertIs(p.attack, attack)
        self.assertFalse(attack.airborne)
        self.assertEqual(p.facing, -1)
        p = Player(350, 102)
        p.vy = -200
        p.request_attack()
        attack = p.attack
        p.update(0.02, 0, False, world)
        self.assertTrue(p.grounded)
        self.assertIs(p.attack, attack)
        self.assertTrue(attack.airborne)

    def test_attack_ends_dash_invulnerability_not_movement(self):
        p = self.player
        p.start_dash()
        p.request_attack()
        self.assertFalse(p.dash_invulnerable)
        self.assertGreater(p.dash_remaining, 0)

    def test_turning_attack_moves_hitbox_without_resetting_hits(self):
        p = self.player
        p.grounded = True
        p.request_attack()
        attack = p.attack
        for elapsed in (.02, .12, .22):
            attack.elapsed = elapsed
            attack.hit_targets.add(self.target)
            p.update(.001, -1, False, World([]))
            self.assertIs(p.attack, attack)
            self.assertEqual(attack.facing, -1)
            self.assertLessEqual(attack.bounds.right, p.x)
            self.assertIn(self.target, attack.hit_targets)
            p.update(.001, 1, False, World([]))
            self.assertEqual(attack.facing, 1)
            self.assertGreaterEqual(attack.bounds.left, p.x + p.width)

    def test_dash_blocked_until_recovery(self):
        p = self.player
        p.grounded = True
        p.request_attack()
        attack = p.attack
        self.assertFalse(p.start_dash())
        attack.advance(0.10)
        self.assertFalse(p.start_dash())
        self.assertEqual(p.dash_charges, 2)
        p.request_attack()
        attack.advance(0.10)
        self.assertTrue(p.start_dash())
        self.assertIsNone(p.attack)
        self.assertFalse(p.attack_queued)

    def test_failed_dash_preserves_recovery_and_queue(self):
        p = self.player
        p.grounded = True
        p.request_attack()
        p.attack.advance(0.20)
        p.request_attack()
        p.dash_charges = 0
        self.assertFalse(p.start_dash())
        self.assertIsNotNone(p.attack)
        self.assertTrue(p.attack_queued)

    def test_game_inputs_damage_reset_and_frame_rates(self):
        import sdl2
        from main import Game
        for fps in (20, 60, 144):
            game = Game()
            game.player.x = 350
            game.inputs.pressed = {sdl2.SDLK_x}
            game.update(1 / fps)
            game.inputs.pressed.clear()
            for _ in range(fps):
                game.update(1 / fps)
            self.assertEqual(game.dummy.hp, 190)
            self.assertIsNone(game.player.attack)
            game.inputs.pressed = {sdl2.SDLK_r}
            game.update(1 / fps)
            self.assertEqual(game.dummy.hp, 200)

    def test_simultaneous_attack_dash_prioritizes_dash(self):
        p = self.player
        p.update(0.01, 0, False, World([]), dash_pressed=True, attack_pressed=True)
        self.assertIsNone(p.attack)
        self.assertEqual(p.dash_charges, 1)

    def test_air_attacks_repeat_without_ground_combo(self):
        p = self.player
        p.request_attack()
        first = p.attack
        p.request_attack()
        p.advance_attack(0.5)
        self.assertIsNot(p.attack, first)
        self.assertTrue(p.attack.airborne)
        self.assertEqual(p.attack.combo_index, 0)


if __name__ == '__main__':
    unittest.main()
