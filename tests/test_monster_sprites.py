import hashlib
import struct
import unittest
from pathlib import Path
from monster_sprites import CATALOG, duration, timed_frame


class MonsterSpriteTests(unittest.TestCase):
    def test_all_sheet_dimensions_and_pivots(self):
        for sheet in CATALOG.values():
            with self.subTest(sheet=sheet['id']):
                data = sheet['file'].read_bytes()
                self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
                width, height = struct.unpack('>II', data[16:24])
                cw, ch = sheet['frame_size']
                self.assertEqual((width, height), (cw * len(sheet['frames']), ch))
                px, py = sheet['pico2d_pivot']
                self.assertTrue(0 <= px <= cw and 0 <= py <= ch)

    def test_deaths_finish_on_clear_frame_once(self):
        for kind in ('jangseung', 'sotdae', 'ember', 'mask', 'onggi',
                     'rice_chest', 'jige', 'hahoe', 'guardian'):
            sheet = kind + '_death'
            self.assertEqual(timed_frame(sheet, 0), 0)
            self.assertEqual(timed_frame(sheet, duration(sheet) + 10), 6)

    def test_supplied_images_preserved(self):
        root = Path(__file__).resolve().parents[1] / 'Sprite_sheet'
        for category in ('Normal', 'Mid', 'Main'):
            for original in (root / 'Monsters_sprite_demo' / category).rglob('*.png'):
                copy = root / 'Monster' / category.lower() / original.relative_to(root / 'Monsters_sprite_demo' / category)
                self.assertEqual(hashlib.sha256(original.read_bytes()).digest(),
                                 hashlib.sha256(copy.read_bytes()).digest())
