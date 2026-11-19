import unittest
from map_route import ROOMS
from player import Player
from main import MapGame
import sdl2


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


class EncounterFlowTests(unittest.TestCase):
    def step(self, game, seconds):
        for _ in range(round(seconds * 60)):
            game.update(1 / 60)
            game.inputs.pressed.clear()

    def clear_active(self, game):
        for enemy in game.enemies:
            enemy.hp = 0
            enemy.on_combat_hit()
        self.step(game, 2)

    def test_gate_blocks_dash_and_high_jump_until_death_animation_finishes(self):
        game = MapGame()
        gate = game.encounters.gate
        for y in (100, 500):
            player = Player(gate.left - 50, y)
            player.update(.2, 1, False, game.world, dash_pressed=True)
            self.assertLessEqual(player.x + player.width, gate.left)
        for enemy in game.enemies:
            enemy.hp = 0
            enemy.on_combat_hit()
        game.update(.02)
        self.assertIn(gate, game.world.solids)
        self.step(game, 2)
        self.assertNotIn(gate, game.world.solids)
        self.assertFalse(game.room_clear)

    def test_second_group_spawns_once_on_entry_then_opens_final_exit(self):
        game = MapGame()
        self.clear_active(game)
        zone = game.stage.encounters[1]
        game.player.x = zone.trigger_x - game.player.width - 1
        game.update(.01)
        self.assertFalse(game.enemies)
        self.assertFalse(game.room_clear)
        game.player.x += 2
        game.update(.01)
        group = list(game.enemies)
        self.assertEqual(len(group), len(zone.spawns))
        self.assertEqual(game.encounters.active_index, 1)
        self.step(game, .2)
        self.assertEqual(game.enemies, group)
        self.clear_active(game)
        self.assertTrue(game.room_clear)
        self.assertEqual(game.encounters.completed, 2)
        game.player.x = 0
        game.update(.02)
        game.player.x = zone.trigger_x
        game.update(.02)
        self.assertFalse(game.enemies)

    def test_restart_resets_groups_and_barriers(self):
        game = MapGame()
        self.clear_active(game)
        game.player.x = game.stage.encounters[1].trigger_x
        game.update(.02)
        old_gate = game.encounters.gate
        game.inputs.pressed = {sdl2.SDLK_r}
        game.update(.02)
        self.assertEqual(game.encounters.active_index, 0)
        self.assertEqual(game.encounters.completed, 0)
        self.assertNotIn(old_gate, game.world.solids)
        self.assertIn(game.encounters.gate, game.world.solids)
        self.assertEqual(len(game.enemies), 2)

    def test_dead_player_cannot_activate_next_group(self):
        game = MapGame()
        self.clear_active(game)
        game.player.hp = 0
        game.player.x = game.stage.encounters[1].trigger_x
        game.update(.02)
        self.assertFalse(game.enemies)
        self.assertIsNone(game.encounters.active_index)
