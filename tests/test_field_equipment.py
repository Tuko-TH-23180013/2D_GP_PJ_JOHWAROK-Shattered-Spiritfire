import unittest
import sdl2
from main import MapGame


class FieldTests(unittest.TestCase):
    def test_full_slots_auto_pause_replace_and_drop(self):
        game = MapGame()
        gear = game.gear
        for i in range(4):
            gear.equipment.equip(i, 'fang')
        drop = gear.add_drop('mirror', game.player, 'reward')
        game.inputs.pressed = {sdl2.SDLK_f}
        before = game.elapsed
        game.update(.1)
        self.assertTrue(gear.open)
        self.assertEqual(game.elapsed, before)
        self.assertIs(gear.pending, drop)
        gear.replace(0, game.player)
        self.assertTrue(drop.consumed)
        self.assertEqual(gear.drops[-1].item_id, 'fang')
        self.assertEqual(gear.equipment.slots[0], 'mirror')

    def test_hold_once_cancel_and_short_duplicate_equip(self):
        game = MapGame()
        gear = game.gear
        gear.equipment.equip(0, 'fang')
        drop = gear.add_drop('fang', game.player)
        game.inputs.pressed = {sdl2.SDLK_f}
        game.inputs.held = {sdl2.SDLK_f}
        gear.update_field(game, .5)
        game.inputs.pressed.clear()
        game.inputs.focus_lost = True
        gear.update_field(game, .5)
        self.assertEqual(game.rewards.gold, 0)
        game.inputs.focus_lost = False
        game.inputs.pressed = {sdl2.SDLK_f}
        gear.update_field(game, .5)
        game.inputs.pressed.clear()
        gear.update_field(game, .5)
        gear.update_field(game, 2)
        self.assertEqual(game.rewards.gold, 10)
        self.assertTrue(drop.consumed)
        self.assertEqual(gear.equipment.slots.count('fang'), 1)
        second = gear.add_drop('fang', game.player)
        game.inputs.pressed = {sdl2.SDLK_f}
        gear.update_field(game, .1)
        game.inputs.pressed.clear()
        game.inputs.held.clear()
        game.inputs.released = {sdl2.SDLK_f}
        gear.update_field(game, .01)
        self.assertTrue(second.consumed)
        self.assertEqual(gear.equipment.slots.count('fang'), 2)

    def test_pause_and_form_lock_includes_future_wave(self):
        game = MapGame()
        game.player.start_dash()
        game.inputs.pressed = {sdl2.SDLK_TAB}
        game.update(.02)
        game.inputs.pressed.clear()
        before = (game.elapsed, game.player.x, game.player.dash_remaining, game.enemies[0].x)
        game.update(100)
        self.assertEqual(before, (game.elapsed, game.player.x, game.player.dash_remaining, game.enemies[0].x))
        self.assertFalse(game.gear.select_form(game, 'giant'))
        game.enemies.clear()
        self.assertFalse(game.gear.can_change_form(game))
        game.enter_room(3)
        game.gear.open = True
        self.assertTrue(game.gear.select_form(game, 'giant'))
        self.assertEqual(game.player.weapon, 'giant')

    def test_death_and_restart_reset_run_but_transition_keeps_equipment(self):
        game = MapGame()
        game.gear.equipment.equip(0, 'red_knot')
        game.player.refresh_stats()
        game.enter_room(1, hp=80)
        self.assertEqual((game.player.hp, game.player.max_hp), (80, 110))
        game.rewards.gold = 20
        game.player.hp = 0
        game.update(.01)
        self.assertEqual(game.rewards.gold, 0)
        self.assertEqual(game.player.max_hp, 100)
        self.assertFalse(any(game.gear.equipment.slots))
        game.restart()
        self.assertEqual(game.room_index, 0)
