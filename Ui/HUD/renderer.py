"""화면 고정형 데모 HUD. SDL 창 생성 이후 로드하며 게임 상태를 읽기만 한다."""
import ctypes
import os
from pathlib import Path

from pico2d import pico2d as p2d
import sdl2
from sdl2.sdlttf import TTF_SizeUTF8

from sprite_animation import ASSET_ROOT
from .model import ASSETS, ratio, dash_levels, boss_visible

PALE = (243, 228, 207)
GOLD = (181, 144, 92)
CYAN = (100, 222, 241)


class HUD:
    def __init__(self):
        self.images = {name: p2d.load_image(str(path)) for name, path in ASSETS.items()}
        for image in self.images.values():
            sdl2.SDL_SetTextureScaleMode(image.texture, sdl2.SDL_ScaleModeNearest)
        # 시스템 한글 폰트는 복제/배포하지 않는다. 없는 환경은 동봉 폰트/영문 사용.
        korean_font = Path(os.environ.get('WINDIR', '')) / 'Fonts' / 'malgun.ttf'
        self.korean = korean_font.is_file()
        font_path = korean_font if self.korean else ASSET_ROOT / 'font.ttf'
        self.font = p2d.load_font(str(font_path), 16)
        self.small = p2d.load_font(str(font_path), 12)
        self.title = p2d.load_font(str(font_path), 21)

    def text(self, x, y, ko, en=None, color=PALE, font=None, centered=False):
        value = ko if self.korean or en is None else en
        font = font or self.font
        if centered:
            width, height = ctypes.c_int(), ctypes.c_int()
            TTF_SizeUTF8(font.font, value.encode('utf-8'), ctypes.byref(width), ctypes.byref(height))
            x -= width.value / 2
        font.draw(round(x + 1), round(y - 1), value, (10, 12, 21))
        font.draw(round(x), round(y), value, color)

    def asset(self, name, x, y, w, h):
        self.images[name].draw(round(x), round(y), round(w), round(h))

    def meter(self, name, left, y, width, height, value):
        filled = round(width * max(0, min(1, value)))
        if filled:
            self.images[name].draw(left + filled / 2, y, filled, height)

    def draw_player(self, player):
        self.asset('player_panel', 220, 50, 422, 94)
        self.asset('portrait_dokkaebi', 58, 53, 84, 84)
        for index, weapon in enumerate(('basic', 'giant')):
            x = 141 + index * 62
            self.asset('slot_active' if player.weapon == weapon else 'slot_inactive', x, 76, 42, 42)
            self.asset('weapon_basic' if weapon == 'basic' else 'weapon_heavy', x, 76, 39, 39)
        self.text(172, 76, '↔', '<>', color=GOLD, centered=True)
        self.text(252, 81, '기본 방망이' if player.weapon == 'basic' else '거대 방망이',
                  'BASIC' if player.weapon == 'basic' else 'GIANT', font=self.small)
        self.text(252, 64, '전환 예약' if player.switch_queued else 'Space · 무기 전환',
                  'Switch queued' if player.switch_queued else 'Space: switch',
                  color=CYAN if player.switch_queued else GOLD, font=self.small)
        self.meter('meter_hp', 120, 40, 268, 9, ratio(player.hp, player.max_hp))
        self.asset('health_frame', 254, 40, 282, 22)
        self.text(254, 40, f'{player.hp} / {player.max_hp}', centered=True, font=self.small)
        for i, level in enumerate(dash_levels(player)):
            x = 130 + 34 * i
            self.asset('dash_empty', x, 16, 24, 28)
            if level > 0:
                image = self.images['dash_ready']
                source_h = max(1, round(image.h * level))
                dest_h = 28 * source_h / image.h
                image.clip_draw(0, 0, image.w, source_h, x, 2 + dest_h / 2, 24, dest_h)
        self.text(191, 16, f'대시 {player.dash_charges}/2', f'Dash {player.dash_charges}/2',
                  color=CYAN, font=self.small)

    def draw_abilities(self):
        self.asset('ability_panel', 624, 50, 150, 90)
        for key, x in (('A', 595), ('S', 653)):
            self.asset('slot_inactive', x, 49, 44, 44)
            self.asset('skill_locked', x, 49, 38, 38)
            self.text(x, 82, key, centered=True, font=self.small)
        self.text(624, 16, '능력 잠김', 'Abilities locked', centered=True, font=self.small, color=GOLD)

    def draw_boss(self, game):
        if not boss_visible(game):
            return
        boss = game.boss
        names = {'hahoe': ('하회탈 수호 무사', 'Hahoe guardian'),
                 'guardian': ('타락한 도깨비 수호신', 'Corrupted guardian')}
        ko, en = names.get(getattr(boss, 'kind', ''), ('오래된 도깨비', 'Old Dokkaebi'))
        self.asset('boss_panel', 640, 658, 650, 83)
        self.text(640, 704, ko, en, font=self.title, centered=True)
        self.meter('meter_boss', 346, 663, 586, 10, ratio(boss.hp, boss.max_hp))
        self.asset('boss_health_frame', 639, 661, 602, 23)
        self.text(640, 662, f'{boss.hp} / {boss.max_hp}', font=self.small, centered=True)
        self.meter('meter_stagger', 397, 632, 484, 5, ratio(boss.stagger, boss.stagger_limit or 0))
        self.asset('boss_stagger_frame', 639, 632, 500, 16)
        state = {'DOWN': ('다운', 'DOWN'), 'WAKE': ('기상', 'WAKE')}.get(boss.state, ('스태거', 'STAGGER'))
        self.text(640, 613, state[0], state[1], font=self.small, centered=True, color=GOLD)

    def draw(self, game):
        p2d.draw_rectangle(0, 0, 1279, 99, 13, 15, 26, filled=True)
        p2d.draw_rectangle(0, 98, 1279, 99, 87, 73, 66, filled=True)
        self.draw_player(game.player)
        self.draw_abilities()
        self.draw_boss(game)
        self.text(775, 71, '방향키 이동  C 점프  ↓+C 하강', 'Arrows move / C jump / Down+C drop', font=self.small)
        self.text(775, 50, 'X 공격  Z 대시  Space 무기 전환', 'X attack / Z dash / Space switch', font=self.small)
        self.text(775, 29, '↑ 상호작용  R 재시작  F2 판정  Esc 종료',
                  'Up interact / R retry / F2 boxes / Esc quit', color=GOLD, font=self.small)
