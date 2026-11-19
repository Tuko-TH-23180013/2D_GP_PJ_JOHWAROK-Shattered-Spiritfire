import unittest
from map_route import ROOMS
from player import Player


class EncounterLayoutTests(unittest.TestCase):
    def test_normal_rooms_have_safe_ordered_battle_sections(self):
        for room in ROOMS:
            if room.category != 'normal':
                continue
            self.assertGreaterEqual(room.width, 3200)
            self.assertEqual(len(room.encounters), 2)
            self.assertEqual(room.spawns, room.encounters[0].spawns)
            previous_gate = -1
            for zone in room.encounters:
                self.assertGreater(zone.trigger_x, previous_gate)
                self.assertLess(zone.trigger_x, zone.gate_x)
                self.assertLess(zone.gate_x, room.boss_entrance.left)
                for kind, x, y in zone.spawns:
                    self.assertGreater(x, zone.trigger_x + 150)
                    self.assertLess(x + 60, zone.gate_x)
                    self.assertGreaterEqual(y, 100)
                previous_gate = zone.gate_x

    def test_traversal_platforms_are_reachable_and_allow_drop(self):
        for room in ROOMS:
            if room.category != 'normal':
                continue
            world = room.create_world()
            platform = next(p for p in room.platforms if p.left >= 1400)
            player = Player(platform.left + 20, 100)
            player.update(.01, 0, True, world)
            highest = player.y
            for step in range(120):
                player.update(.01, 0, step == 20, world)
                highest = max(highest, player.y)
            self.assertGreater(highest, platform.top)
            self.assertAlmostEqual(player.y, platform.top)
            player.update(.02, 0, True, world, down_held=True)
            for _ in range(100):
                player.update(.01, 0, False, world)
            self.assertAlmostEqual(player.y, 100)
