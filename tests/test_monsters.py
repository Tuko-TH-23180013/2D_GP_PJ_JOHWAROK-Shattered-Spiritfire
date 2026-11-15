import unittest
from attack import Attack
from combat_system import CombatSystem
from monsters import Monster, SPECS, Spiritfire
from player import Player
from world import World, Rect


class MonsterTests(unittest.TestCase):
    def setUp(self):
        self.world = World([Rect(0, 0, 1600, 100), Rect(1600, 0, 1640, 720)])
        self.player = Player(580, 100)

    def advance(self, monster, seconds):
        for _ in range(round(seconds * 240)):
            monster.update(1 / 240, self.player, self.world)

    def test_all_patterns_finish_and_lock_direction(self):
        for kind in SPECS:
            with self.subTest(kind=kind):
                enemy = Monster(kind, 500, 180 if kind == 'sotdae' else 100)
                enemy.update(.001, self.player, self.world)
                self.assertIsNotNone(enemy.attack)
                attack = enemy.attack
                self.player.x = 0
                self.advance(enemy, .1)
                self.assertEqual(attack.facing, 1)
                self.assertEqual(enemy.facing, 1)
                self.advance(enemy, 1.8)
                self.assertIsNot(enemy.attack, attack)
                self.player.x = 580

    def test_ember_emits_one_independent_projectile(self):
        enemy = Monster('ember', 500, 100)
        self.advance(enemy, .8)
        self.assertEqual(len(enemy.projectiles), 1)
        shot = enemy.projectiles[0]
        x = shot.x
        enemy.x -= 30
        shot.update(.1, self.world)
        self.assertAlmostEqual(shot.x, x + 31)
        enemy.hp = 0
        enemy.on_combat_hit()
        shot.update(.01, self.world)
        self.assertEqual(shot.phase, 'DONE')
        self.assertEqual(enemy.projectiles, [])

    def test_projectile_hits_once_and_stops_at_wall(self):
        enemy = Monster('ember', 500)
        enemy.facing = 1
        shot = Spiritfire(enemy)
        shot.x = self.player.x
        combat = CombatSystem()
        combat.resolve([shot], [self.player])
        self.assertEqual(self.player.hp, 88)
        shot.update(.01, self.world)
        self.assertEqual(shot.phase, 'DONE')
        shot = Spiritfire(enemy)
        shot.x = 1570
        shot.update(.1, self.world)
        self.assertEqual(shot.phase, 'DONE')
        self.assertLessEqual(shot.x + shot.width, 1600)

    def test_charge_stops_at_ledge_and_wall(self):
        for world in (World([Rect(0, 0, 600, 100)]), self.world):
            enemy = Monster('jige', 550 if world is not self.world else 1550)
            enemy.facing = 1
            enemy.attack = Attack(enemy, enemy.spec.attack)
            enemy.attack.elapsed = enemy.spec.attack.startup
            enemy.update(.1, self.player, world)
            self.assertEqual(enemy.attack.phase, 'RECOVERY')
            self.assertLessEqual(enemy.x + enemy.width, 600 if world is not self.world else 1600)

    def test_death_freezes_position_until_animation_finishes(self):
        for kind in SPECS:
            enemy = Monster(kind, 500, 170)
            enemy.hp = 0
            enemy.on_combat_hit()
            self.advance(enemy, .1)
            self.assertEqual((enemy.x, enemy.y), (500, 170))
            self.assertIsNone(enemy.attack)
            self.assertFalse(enemy.death_done)
            self.advance(enemy, 2)
            self.assertTrue(enemy.death_done)

    def test_dive_target_is_captured_during_startup(self):
        enemy = Monster('sotdae', 500, 250)
        enemy.update(.001, self.player, self.world)
        velocity = enemy.dive_velocity
        self.player.x = 300
        self.advance(enemy, .7)
        self.assertEqual(enemy.dive_velocity, velocity)
        self.assertGreater(enemy.x, 500)

    def test_rice_burst_one_hit_per_attack(self):
        enemy = Monster('rice_chest', 500)
        enemy.facing = 1
        attack = Attack(enemy, enemy.spec.attack)
        attack.elapsed = attack.data.startup
        combat = CombatSystem()
        for _ in range(10):
            combat.begin_frame()
            self.player.hurt_invulnerability = 0
            combat.resolve([attack], [self.player])
        self.assertEqual(self.player.hp, 86)
