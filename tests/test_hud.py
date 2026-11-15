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
