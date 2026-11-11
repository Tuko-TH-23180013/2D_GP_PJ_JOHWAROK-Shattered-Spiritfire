import unittest
from boss import Boss
from player import Player
from world import World, Rect
from combat_system import CombatSystem
from attack import Attack, BASIC_COMBO


class BossTests(unittest.TestCase):
    def test_down_wake_damage_and_repeat_recovery(self):
        boss, player, combat = Boss(400), Player(300), CombatSystem()
        world = World()
        for cycle in range(2):
            boss.cooldown = 0
            boss.update(0.01, player, world)
            for _ in range(8):
                attack = Attack(player, BASIC_COMBO[0])
                attack.advance(0.1)
                combat.begin_frame()
                combat.resolve([attack], [boss])
            self.assertEqual(boss.state, 'DOWN')
            self.assertIsNone(boss.attack)
            hp = boss.hp
            attack = Attack(player, BASIC_COMBO[0])
            attack.advance(0.1)
            combat.begin_frame()
            combat.resolve([attack], [boss])
            self.assertEqual(boss.hp, hp - 10)
            self.assertEqual(boss.stagger, 120)
            combat.update_target(boss, 2.01)
            boss.update(0.01, player, world)
            self.assertEqual(boss.state, 'WAKE')
            attack = Attack(player, BASIC_COMBO[0])
            attack.advance(0.1)
            combat.begin_frame()
            combat.resolve([attack], [boss])
            self.assertEqual(boss.hp, hp - 20)
            self.assertEqual(boss.stagger, 0)
            boss.update(0.71, player, world)
            self.assertEqual(boss.state, 'NORMAL')

    def test_lethal_hit_while_down_clears_attack(self):
        boss, player = Boss(400), Player(300)
        boss.hp = 5
        boss.state = 'DOWN'
        boss.stagger_remaining = 1
        attack = Attack(player, BASIC_COMBO[0])
        attack.advance(0.1)
        CombatSystem().resolve([attack], [boss])
        self.assertEqual(boss.state, 'DEAD')
        self.assertEqual(boss.hp, 0)
        self.assertIsNone(boss.attack)

    def test_patterns_alternate_and_have_windup(self):
        boss, player = Boss(400), Player(300)
        world = World([Rect(0, 0, 1000, 100)])
        seen = []
        previous = None
        for _ in range(1000):
            boss.update(0.01, player, world)
            if boss.attack is not None and boss.attack is not previous:
                seen.append(boss.pattern)
                self.assertEqual(boss.attack.phase, 'STARTUP')
                self.assertGreaterEqual(boss.attack.data.startup, 0.6)
                previous = boss.attack
            if len(seen) == 3:
                break
        self.assertEqual(seen, ['SWING', 'RUSH', 'SWING'])

    def test_rush_moves_only_active_and_stops_at_wall(self):
        boss, player = Boss(400), Player(300)
        world = World([Rect(0, 0, 1000, 100), Rect(200, 100, 220, 300)])
        boss.pattern_index = 1
        boss.cooldown = 0
        boss.update(0.01, player, world)
        for _ in range(50):
            boss.update(0.01, player, world)
        self.assertEqual(boss.x, 400)
        for _ in range(100):
            boss.update(0.01, player, world)
        self.assertEqual(boss.x, 220)

    def test_normal_hit_does_not_cancel_pattern(self):
        boss, player = Boss(400), Player(300)
        boss.cooldown = 0
        boss.update(0.01, player, World())
        current = boss.attack
        attack = Attack(player, BASIC_COMBO[0])
        attack.advance(0.1)
        CombatSystem().resolve([attack], [boss])
        self.assertEqual(boss.hp, 490)
        self.assertIs(boss.attack, current)
