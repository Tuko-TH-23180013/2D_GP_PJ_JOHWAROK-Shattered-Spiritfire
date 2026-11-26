import unittest
from equipment import Equipment
from player import Player
from combat_system import CombatSystem
from attack import Attack, BASIC_COMBO
from training_dummy import TrainingDummy


class EquipmentTests(unittest.TestCase):
    def test_duplicate_threshold_and_bonus_only_once(self):
        gear = Equipment()
        for index, expected in enumerate((.05, .20, .25, .30)):
            gear.equip(index, 'fang')
            self.assertAlmostEqual(gear.calculate().attack, expected)
            self.assertEqual(gear.counts()['맹공'], index + 1)

    def test_recalculate_replace_remove_no_growth_or_free_heal(self):
        player = Player()
        for _ in range(100):
            player.equipment.equip(0, 'guard_knot')
            player.refresh_stats()
            self.assertEqual((player.hp, player.max_hp), (100, 115))
            player.equipment.equip(0, 'fang')
            player.refresh_stats()
            self.assertEqual(player.max_hp, 100)
            self.assertAlmostEqual(player.damage_multiplier, 1.05)
        player.equipment.equip(0, None)
        player.refresh_stats()
        self.assertEqual(player.damage_multiplier, 1)

    def test_stats_reach_combat(self):
        player, dummy = Player(), TrainingDummy()
        player.equipment.equip(0, 'fang')
        player.equipment.equip(1, 'fang')
        player.refresh_stats()
        dummy.x, dummy.y = player.x + player.width, player.y
        attack = Attack(player, BASIC_COMBO[0])
        attack.advance(.10)
        before = dummy.hp
        CombatSystem().resolve([attack], [dummy])
        self.assertEqual(before - dummy.hp, 12)
