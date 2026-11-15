import unittest
from demo_bosses import Hahoe, Guardian
from player import Player
from world import World, Rect
from combat_system import CombatSystem
from monster_sprites import pose


class DemoBossTests(unittest.TestCase):
    def setUp(self):
        self.world = World([Rect(0, 0, 1600, 100), Rect(1600, 0, 1640, 720)])
        self.player = Player(600, 100)

    def test_hahoe_distance_selects_pattern(self):
        for distance, pattern in ((80, 'SLASH'), (180, 'THRUST')):
            boss = Hahoe(500)
            boss.cooldown = 0
            self.player.x = 500 + distance
            boss.update(.01, self.player, self.world)
            self.assertEqual(boss.pattern, pattern)
            attack = boss.attack
            boss.hit_flash = .1
            boss.on_combat_hit()
            self.assertIs(boss.attack, attack)
            self.assertEqual(pose(boss)[1], 2)

    def test_hahoe_down_wake_and_death(self):
        boss = Hahoe(500)
        boss.stagger_remaining = boss.stagger_duration
        boss.on_combat_hit()
        self.assertEqual(pose(boss), ('hahoe_reactions', 1))
        combat = CombatSystem()
        combat.update_target(boss, 2)
        boss.update(.01, self.player, self.world)
        self.assertEqual(boss.state, 'WAKE')
        self.assertFalse(boss.can_accumulate_stagger)
        self.assertEqual(pose(boss), ('hahoe_reactions', 2))
        boss.update(.7, self.player, self.world)
        self.assertEqual(boss.state, 'NORMAL')
        boss.hp = 0
        boss.on_combat_hit()
        boss.update(.1, self.player, self.world)
        self.assertEqual(pose(boss)[0], 'hahoe_death')
        self.assertFalse(boss.death_done)
        boss.update(2, self.player, self.world)
        self.assertTrue(boss.death_done)

    def test_guardian_alternates_and_wall_ends_rush(self):
        boss = Guardian(500)
        boss.cooldown = 0
        boss.update(.01, self.player, self.world)
        self.assertEqual(boss.sheet, 'guardian_sweep')
        boss.update(1.5, self.player, self.world)
        boss.update(.5, self.player, self.world)
        self.assertEqual(boss.sheet, 'guardian')
        self.assertEqual(boss.pattern, 'RUSH')
        boss.x = 1500
        boss.attack.facing = 1
        boss.attack.elapsed = boss.attack.data.startup
        boss.update(.1, self.player, self.world)
        self.assertEqual(boss.attack.phase, 'RECOVERY')
        self.assertLessEqual(boss.x + boss.width, 1600)

    def test_guardian_reactions_and_sweep_hold(self):
        boss = Guardian(500)
        boss.cooldown = 0
        boss.update(.01, self.player, self.world)
        first_pose = pose(boss)
        boss.update(.3, self.player, self.world)
        self.assertNotEqual(pose(boss), first_pose)
        boss.stagger_remaining = 2
        boss.on_combat_hit()
        self.assertEqual(pose(boss), ('guardian_reactions', 2))
        boss.hp = 0
        boss.on_combat_hit()
        boss.update(.1, self.player, self.world)
        self.assertEqual(pose(boss)[0], 'guardian_death')
