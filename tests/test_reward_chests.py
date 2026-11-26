import unittest
import sdl2
from main import MapGame
from reward_chest import RewardChest
from reward_chest_ui import handle_clicks, details


class ChestTests(unittest.TestCase):
    def test_spawn_once_and_reopen_keeps_choices_and_pauses(self):
        game = MapGame()
        game.encounters.completed = 1
        game.gear.award(game)
        game.gear.award(game)
        self.assertEqual(len(game.gear.chests),2)
        chest = game.gear.chests[0]
        game.player.x = chest.x
        before = game.elapsed
        game.inputs.pressed = {sdl2.SDLK_f}
        game.update(.02)
        self.assertIs(game.gear.chest_open,chest)
        game.inputs.pressed.clear()
        game.update(10)
        self.assertEqual(game.elapsed,before)
        choices = chest.choices
        game.inputs.pressed = {sdl2.SDLK_TAB}
        game.update(.02)
        game.inputs.pressed = {sdl2.SDLK_f}
        game.update(.02)
        self.assertEqual(game.gear.chest_open.choices,choices)

    def test_mouse_selection_required_and_claim_only_once(self):
        game = MapGame()
        chest = RewardChest('item',('fang',),100)
        game.gear.chests.append(chest)
        game.gear.chest_open = chest
        game.inputs.clicks = [(640,200)]
        handle_clicks(game)
        self.assertFalse(chest.claimed)
        game.inputs.clicks = [(600,460),(640,200),(640,200)]
        handle_clicks(game)
        self.assertTrue(chest.claimed)
        self.assertEqual(game.gear.equipment.slots.count('fang'),1)
        self.assertFalse(chest.claim(game))

    def test_full_inventory_cancel_retains_delivered_item(self):
        game = MapGame()
        game.gear.equipment.slots = ['fang']*4
        chest = RewardChest('item',('mirror',),100,selected=0)
        game.gear.chest_open = chest
        chest.claim(game)
        self.assertTrue(game.gear.open)
        drop = game.gear.pending
        game.gear.toggle()
        self.assertFalse(drop.consumed)
        self.assertIn(drop,game.gear.drops)
        self.assertTrue(chest.claimed)

    def test_duplicate_on_floor_and_ability_info(self):
        game = MapGame()
        game.gear.equipment.equip(0,'fang')
        chest = RewardChest('item',('fang',),100,selected=0)
        game.gear.chest_open = chest
        chest.claim(game)
        self.assertEqual(game.gear.equipment.slots.count('fang'),1)
        self.assertFalse(game.gear.drops[-1].consumed)
        for name in ('enlarge','blink'):
            lines = details(RewardChest('ability',(name,),100),0)
            self.assertGreaterEqual(len(lines),4)

    def test_chests_reset_on_new_run(self):
        game = MapGame()
        game.encounters.completed = 1
        game.gear.award(game)
        game.restart()
        self.assertFalse(game.gear.chests)
        self.assertIsNone(game.gear.chest_open)
