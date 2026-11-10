import unittest

from player import Player
from weapon_data import WEAPONS


class WeaponTests(unittest.TestCase):
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
