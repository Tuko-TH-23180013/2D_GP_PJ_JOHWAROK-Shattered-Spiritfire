import unittest
import sdl2
from main import MapGame
from map_route import ROOMS
from monsters import SPECS, Spiritfire
from attack import Attack, AttackData


class MapRouteTests(unittest.TestCase):
    def step(self, game, seconds):
        for _ in range(round(seconds * 60)):
            game.update(1 / 60)
            game.inputs.pressed.clear()

    def defeat_room(self, game):
        for _ in range(4):
            for actor in game.enemies + ([game.boss] if game.boss else []):
                actor.hp = 0
                actor.on_combat_hit()
            self.step(game, 2)
            if game.room_clear:
                return
            if game.encounters.active_index is None:
                zone = game.encounters.zones[game.encounters.next_index]
                game.player.x, game.player.y = zone.trigger_x, 100
                self.step(game, .1)
        self.fail('room did not finish')

    def exit_room(self, game):
        game.player.x = game.stage.width - 115
        game.player.y = 100
        game.inputs.pressed = {sdl2.SDLK_f}
        game.update(.02)

    def test_route_contains_all_monsters_and_requested_order(self):
        self.assertEqual([r.category for r in ROOMS], ['normal', 'normal', 'mid', 'save', 'normal', 'normal', 'main'])
        self.assertEqual({kind for r in ROOMS for kind, x, y in r.spawns}, set(SPECS))

    def test_exit_requires_clear_and_preserves_hp_weapon(self):
        game = MapGame()
        self.exit_room(game)
        self.assertEqual(game.room_index, 0)
        self.defeat_room(game)
        game.player.hp = 65
        game.player.weapon = 'giant'
        self.exit_room(game)
        self.assertEqual(game.room_index, 1)
        self.assertEqual(game.player.hp, 65)
        self.assertEqual(game.player.weapon, 'giant')
        self.assertIsNone(game.player.attack)
        self.assertFalse(game.inputs.pressed or game.inputs.held)
        self.assertEqual(game.camera.x, 0)

    def test_full_route_mid_does_not_win_main_does(self):
        game = MapGame()
        for index in range(7):
            self.assertEqual(game.room_index, index)
            self.defeat_room(game)
            self.assertTrue(game.room_clear)
            self.assertEqual(game.victory, index == 6)
            if index != 6:
                self.exit_room(game)
        self.assertEqual(game.cleared_rooms, set(range(7)))

    def test_death_animation_gates_exit(self):
        game = MapGame()
        for actor in game.enemies:
            actor.hp = 0
            actor.on_combat_hit()
        self.exit_room(game)
        self.assertEqual(game.room_index, 0)
        self.assertFalse(game.room_clear)
        self.step(game, 2)
        self.defeat_room(game)
        self.exit_room(game)
        self.assertEqual(game.room_index, 1)

    def test_restart_cleans_run_even_after_old_checkpoint(self):
        game = MapGame()
        game.enter_room(3)
        game.player.x = 640
        game.inputs.pressed = {sdl2.SDLK_f}
        game.update(.02)
        self.assertEqual(game.saved_room, 3)
        self.exit_room(game)
        game.projectiles.append(Spiritfire(game.enemies[0]))
        game.player.hp = 0
        game.inputs.pressed = {sdl2.SDLK_r}
        game.update(.02)
        self.assertEqual(game.room_index, 0)
        self.assertEqual(game.player.x, 100)
        self.assertEqual(game.player.hp, 100)
        self.assertEqual(game.player.dash_charges, 2)
        self.assertEqual(game.cleared_rooms, set())
        self.assertFalse(game.checkpoint.active)
        self.assertEqual(game.projectiles, [])
        self.exit_room(game)
        self.assertEqual(len(game.enemies), 2)

    def test_unsaved_restart_returns_to_beginning(self):
        game = MapGame()
        game.enter_room(4)
        game.restart()
        self.assertEqual(game.room_index, 0)
        self.assertEqual(len(game.enemies), 2)
        self.assertFalse(game.checkpoint.active)

    def test_every_room_has_walkable_spawn_to_exit(self):
        for index in range(7):
            game = MapGame()
            game.enter_room(index)
            game.enemies.clear()
            if game.encounters.gate is not None:
                game.world.solids.remove(game.encounters.gate)
            from encounter_flow import EncounterFlow
            game.encounters = EncounterFlow((), game.world)
            game.boss = None
            game.boss_active = False
            game.inputs.held = {sdl2.SDLK_RIGHT}
            # 최종 방에서도 경로를 검사하도록 승리 정지만 해제한다.
            for _ in range(round(game.stage.width / 300 * 60) + 60):
                game.victory = False
                game.update(1 / 60)
            self.assertGreaterEqual(game.player.x + game.player.width, game.stage.boss_entrance.left)
            self.assertGreaterEqual(game.player.y, 100)

    def test_combat_kills_and_enemy_projectile_uses_real_damage(self):
        game = MapGame()
        actor = game.enemies[0]
        game.player.x = actor.x - game.player.width
        game.player.facing = 1
        game.player.attack = Attack(game.player, AttackData('fixture', 0, .1, .1, 999, 0, 100, 100))
        game.update(.02)
        self.assertEqual(actor.hp, 0)
        self.assertIn(actor, game.enemies)
        self.assertIsNone(actor.attack)
        game.enter_room(4)
        ember = game.enemies[0]
        game.player.x = ember.x - 150
        self.step(game, 1.2)
        self.assertLess(game.player.hp, 100)

    def test_player_death_cancels_attacks_and_shots(self):
        game = MapGame()
        actor = game.enemies[0]
        actor.facing = -1
        game.player.x = actor.x - 50
        game.player.hp = 1
        actor.attack = Attack(actor, actor.spec.attack)
        actor.attack.elapsed = actor.spec.attack.startup
        game.update(.02)
        self.assertEqual(game.player.hp, 0)
        self.assertTrue(all(e.attack is None for e in game.enemies))
        self.assertFalse(game.projectiles)

    def test_projectile_damage_consistent_across_frame_rates(self):
        results = []
        for fps in (20, 60, 144):
            game = MapGame()
            game.enter_room(4)
            game.player.x = game.enemies[0].x - 150
            for _ in range(round(1.5 * fps)):
                game.update(1 / fps)
            results.append(game.player.hp)
        self.assertEqual(results, [88, 88, 88])
