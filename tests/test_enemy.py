import unittest
from enemy import Enemy
from player import Player
from world import World
from attack import Attack, BASIC_COMBO
from combat_system import CombatSystem
from enemy import ENEMY_ATTACK


class EnemyTests(unittest.TestCase):
    def test_dead_enemy_cannot_damage_or_act(self):
        p, e, combat = Player(820), Enemy(), CombatSystem()
        e.update(0.01, p, World())
        old_attack = e.attack
        old_attack.advance(0.5)
        e.hp = 0
        e.on_combat_hit()
        combat.resolve([old_attack], [p])
        e.update(0.01, p, World())
        self.assertEqual(p.hp, 100)
        self.assertIsNone(e.attack)
        self.assertEqual(e.state, 'DEAD')

    def test_lethal_hit_clears_player_actions(self):
        p, e, combat = Player(820), Enemy(), CombatSystem()
        p.request_attack()
        p.request_attack()
        p.request_switch()
        p.hp = 10
        attack = Attack(e, ENEMY_ATTACK)
        attack.advance(0.45)
        combat.resolve([attack], [p])
        self.assertEqual(p.hp, 0)
        self.assertIsNone(p.attack)
        self.assertFalse(p.attack_queued or p.switch_queued)
        self.assertFalse(p.start_dash())
        p.request_attack()
        self.assertIsNone(p.attack)

    def test_death_and_restart_clear_everything(self):
        from main import Game
        import sdl2
        game = Game()
        for _ in range(5):
            game.player.x = 820
            game.player.hp = 15
            for _ in range(120):
                game.update(1 / 60)
            self.assertEqual(game.player.hp, 0)
            old = game.player
            game.inputs.held = {sdl2.SDLK_RIGHT}
            game.inputs.pressed = {sdl2.SDLK_r, sdl2.SDLK_x, sdl2.SDLK_SPACE}
            game.update(1 / 60)
            self.assertIsNot(game.player, old)
            self.assertEqual((game.player.x, game.player.hp, game.player.dash_charges), (120, 100, 2))
            self.assertEqual(len(game.enemies), 1)
            self.assertEqual(game.enemies[0].hp, 120)
            self.assertFalse(game.inputs.held or game.inputs.pressed)
            self.assertIsNone(game.player.attack)
            self.assertFalse(game.player.switch_queued)

    def test_game_removes_killed_enemy_and_prevents_counterattack(self):
        from main import Game
        import sdl2
        game = Game()
        game.player.x = 820
        game.enemies[0].hp = 10
        game.inputs.pressed = {sdl2.SDLK_x}
        game.update(0.05)
        game.inputs.pressed.clear()
        for _ in range(30):
            game.update(0.05)
        self.assertEqual(game.enemies, [])
        self.assertEqual(game.player.hp, 100)

    def test_damage_keeps_player_attack_and_combo(self):
        p, e, combat = Player(820), Enemy(), CombatSystem()
        p.grounded = True
        p.request_attack()
        p.request_attack()
        current = p.attack
        attack = Attack(e, ENEMY_ATTACK)
        attack.advance(0.45)
        combat.resolve([attack], [p])
        self.assertEqual(p.hp, 85)
        self.assertIs(p.attack, current)
        self.assertTrue(p.attack_queued)
        self.assertGreater(p.hurt_invulnerability, 0)

    def test_hurt_invulnerability_blocks_followup_then_expires(self):
        p, e, combat = Player(820), Enemy(), CombatSystem()
        for expected in (85, 85):
            attack = Attack(e, ENEMY_ATTACK)
            attack.advance(0.45)
            combat.begin_frame()
            combat.resolve([attack], [p])
            self.assertEqual(p.hp, expected)
        combat.update_target(p, 0.51)
        combat.begin_frame()
        combat.resolve([attack], [p])
        self.assertEqual(p.hp, 70)

    def test_normal_hits_preserve_enemy_attack_until_stagger(self):
        e, p, combat = Enemy(), Player(820), CombatSystem()
        e.update(0.01, p, World())
        current = e.attack
        for index in range(4):
            attack = Attack(p, BASIC_COMBO[0])
            attack.advance(0.1)
            combat.begin_frame()
            combat.resolve([attack], [e])
            if index < 3:
                self.assertIs(e.attack, current)
        self.assertEqual(e.state, 'STAGGER')
        self.assertIsNone(e.attack)
        combat.update_target(e, 0.61)
        self.assertEqual(e.stagger, 0)

    def test_dash_and_switch_block_enemy_damage(self):
        for action in ('start_dash', 'request_switch'):
            p, e, combat = Player(820), Enemy(), CombatSystem()
            getattr(p, action)()
            attack = Attack(e, ENEMY_ATTACK)
            attack.advance(0.45)
            combat.resolve([attack], [p])
            self.assertEqual(p.hp, 100)

    def test_idle_chase_attack_and_new_attack_instance(self):
        e, p, world = Enemy(), Player(), World()
        e.update(0.01, p, world)
        self.assertEqual(e.state, 'IDLE')
        p.x = 500
        e.update(0.01, p, world)
        self.assertEqual(e.state, 'CHASE')
        self.assertLess(e.x, 900)
        p.x = 820
        e.update(0.01, p, world)
        first = e.attack
        self.assertEqual(first.phase, 'STARTUP')
        for _ in range(160):
            e.update(0.01, p, world)
        self.assertIsNotNone(e.attack)
        self.assertIsNot(e.attack, first)

    def test_preparation_is_visible_and_facing_locked(self):
        e, p, world = Enemy(), Player(820, 100), World()
        e.update(0.01, p, world)
        p.x = 1000
        for _ in range(20):
            e.update(0.01, p, world)
        self.assertEqual(e.attack.phase, 'STARTUP')
        self.assertEqual(e.attack.facing, -1)

    def test_enemy_respects_wall(self):
        e, p, world = Enemy(1000), Player(1200), World()
        for _ in range(100):
            e.update(0.01, p, world)
        self.assertLessEqual(e.x + e.width, 1070)
