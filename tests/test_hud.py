import hashlib
from pathlib import Path
import unittest
from Ui.HUD.model import ASSETS, ratio, dash_levels, boss_visible
from player import Player
from settings import DASH_RECHARGE


class HUDTests(unittest.TestCase):
    def test_assets_are_unchanged_supplied_pngs(self):
        source = Path(__file__).resolve().parents[1] / 'UI_DEMO/JOHWAROK_HUD_v0_3/assets'
        self.assertEqual(set(ASSETS), {p.stem for p in source.glob('*.png')})
        for name, path in ASSETS.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(),
                             hashlib.sha256((source / (name + '.png')).read_bytes()).digest())

    def test_meter_values_clamp(self):
        for value, maximum, expected in ((0, 100, 0), (50, 100, .5), (120, 100, 1), (-2, 100, 0), (1, 0, 0)):
            self.assertEqual(ratio(value, maximum), expected)

    def test_dash_shows_only_next_charge_recovering(self):
        p = Player()
        self.assertEqual(dash_levels(p), (1, 1))
        p.dash_charges = 0
        p.recharge_remaining = DASH_RECHARGE / 2
        self.assertEqual(dash_levels(p), (.5, 0))
        p.dash_charges = 1
        self.assertEqual(dash_levels(p), (1, .5))

    def test_boss_hidden_on_death_or_inactive(self):
        from main import MapGame
        game = MapGame()
        self.assertFalse(boss_visible(game))
        game.enter_room(2)
        self.assertTrue(boss_visible(game))
        game.boss.hp = 0
        self.assertFalse(boss_visible(game))

    def test_player_render_reads_real_state_without_mutation(self):
        from unittest.mock import Mock
        from Ui.HUD.renderer import HUD
        hud = HUD.__new__(HUD)
        hud.asset = Mock()
        hud.text = Mock()
        hud.meter = Mock()
        hud.small = Mock()
        hud.images = {'dash_ready': Mock(w=36, h=45)}
        p = Player()
        p.hp = 37
        p.weapon = 'giant'
        p.switch_queued = True
        p.dash_charges = 1
        p.recharge_remaining = DASH_RECHARGE / 2
        before = vars(p).copy()
        hud.draw_player(p)
        self.assertEqual(vars(p), before)
        hud.asset.assert_any_call('slot_active', 203, 76, 42, 42)
        hud.asset.assert_any_call('slot_inactive', 141, 76, 42, 42)
        hud.meter.assert_called_once_with('meter_hp', 120, 40, 268, 9, .37)

    def test_boss_render_reads_hp_stagger_and_hides_on_death(self):
        from unittest.mock import Mock
        from Ui.HUD.renderer import HUD
        from main import MapGame
        hud = HUD.__new__(HUD)
        hud.asset, hud.text, hud.meter = Mock(), Mock(), Mock()
        hud.small, hud.title = Mock(), Mock()
        game = MapGame()
        for index in (2, 6):
            game.enter_room(index)
            game.boss.hp = game.boss.max_hp / 2
            game.boss.stagger = game.boss.stagger_limit / 4
            before = vars(game.boss).copy()
            hud.draw_boss(game)
            self.assertEqual(vars(game.boss), before)
            hud.meter.assert_any_call('meter_boss', 346, 663, 586, 10, .5)
            hud.meter.assert_any_call('meter_stagger', 397, 632, 484, 5, .25)
            hud.asset.reset_mock()
            game.boss.hp = 0
            hud.draw_boss(game)
            hud.asset.assert_not_called()
