import unittest
from enemy import Enemy
from player import Player
from world import World


class EnemyTests(unittest.TestCase):
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
