"""화면 고정형 데모 HUD. SDL 창 생성 이후 로드하며 게임 상태를 읽기만 한다."""
import ctypes
import os
from pathlib import Path

from pico2d import pico2d as p2d
import sdl2
from sdl2.sdlttf import TTF_SizeUTF8

from sprite_animation import ASSET_ROOT
from .model import ASSETS, ratio, dash_levels, boss_visible
from .location import ROOM_NAMES

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

    def draw_location(self, game):
        index = getattr(game, 'room_index', None)
        # 동봉 빈 재화 패널의 장식 테두리를 지역 표시에 재사용한다.
        self.asset('currency_panel', 1145, 674, 236, 76)
        self.text(1145, 692, '장승마을' + (f' · {index + 1}/7' if index is not None else ''),
                  'Jangseung village' + (f' · {index + 1}/7' if index is not None else ''),
                  centered=True, color=GOLD)
        name = ROOM_NAMES[index] if index is not None else '장승마을'
        self.text(1145, 664, name, game.stage.region_at(game.player.x), centered=True, font=self.small)
        if index is None:
            return
        labels = ('1', '2', '중', '쉼', '3', '4', '보')
        english = ('1', '2', 'M', 'S', '3', '4', 'B')
        for i in range(7):
            x = 1049 + i * 32
            color = CYAN if i == index else GOLD if i in game.cleared_rooms else (75, 77, 90)
            p2d.draw_rectangle(x - 12, 602, x + 12, 626, *color)
            self.text(x, 614, labels[i], english[i], centered=True, font=self.small, color=color)
        if game.stage.category == 'save':
            ko, en = (('세이브 활성 · R 복귀', 'Save active / R respawn') if game.checkpoint.active
                      else ('장승 앞에서 ↑ 저장', 'UP at shrine to save'))
        elif game.room_clear:
            ko, en = ('전투 완료', 'Battle complete') if game.victory else ('출구 열림 · ↑ 이동', 'Exit open / UP to enter')
        else:
            alive = sum(e.hp > 0 for e in game.enemies) + int(game.boss is not None and game.boss.hp > 0)
            flow = getattr(game, 'encounters', None)
            if flow is not None and flow.zones and flow.active_index is None:
                ko, en = '구역 정리 · 오른쪽으로 이동', 'Area clear / Continue right'
            elif flow is not None and flow.zones:
                number, total = flow.active_index + 1, len(flow.zones)
                ko, en = f'전투 {number}/{total} · 남은 적 {alive}', f'Battle {number}/{total} / Enemies {alive}'
            else:
                ko, en = f'남은 적 {alive} · 출구 잠김', f'Enemies {alive} / Exit locked'
        self.text(1145, 581, ko, en, centered=True, font=self.small, color=GOLD)
        self.draw_stage_progress(game)

    def draw_stage_progress(self, game):
        flow = getattr(game, 'encounters', None)
        if flow is None or not flow.zones:
            return
        left, width, y = 1040, 210, 552
        p2d.draw_rectangle(left, y - 2, left + width, y + 2, 50, 55, 68, filled=True)
        for i, zone in enumerate(flow.zones):
            a = left + width * zone.trigger_x / game.stage.width
            b = left + width * zone.gate_x / game.stage.width
            color = CYAN if i < flow.completed else GOLD if i == flow.active_index else (70, 70, 90)
            p2d.draw_rectangle(a, y - 3, b, y + 3, *color, filled=True)
        x = left + width * ratio(game.player.x + game.player.width / 2, game.stage.width)
        p2d.draw_rectangle(x - 2, y - 7, x + 2, y + 7, *PALE, filled=True)
        self.text(1145, 532, f'전투 구역 {flow.completed}/{len(flow.zones)} 완료',
                  f'Areas cleared {flow.completed}/{len(flow.zones)}', centered=True, font=self.small, color=GOLD)

    def draw_notifications(self, game):
        if game.victory:
            self.text(640, 380, '수호신 격파', 'VICTORY', centered=True, font=self.title, color=CYAN)
            self.text(640, 335, 'R 다시 도전 · Esc 종료', 'R retry / Esc quit', centered=True)
        elif game.player.hp <= 0:
            self.text(640, 405, '혼불이 꺼졌습니다', 'YOU DIED', centered=True, color=(255, 170, 180))
            self.text(640, 316, 'R 체크포인트에서 재시작', 'R restart from checkpoint', centered=True, font=self.small)
        elif hasattr(game, 'room_index'):
            flow = getattr(game, 'encounters', None)
            if flow is not None and flow.gate is not None:
                gx, gy = game.camera.screen_point(flow.gate.left, 310)
                if 60 < gx < 1220:
                    self.text(gx, gy, '적을 처치하면 개방', 'Defeat enemies to open', centered=True, font=self.small, color=CYAN)
            gate = game.stage.boss_entrance
            x, y = game.camera.screen_point((gate.left + gate.right) / 2, gate.top + 24)
            x = max(70, min(1210, x))
            if gate.right >= game.camera.x and gate.left <= game.camera.x + game.camera.visible_width:
                self.text(x, y, '↑ 다음 맵' if game.room_clear else '잠김',
                          'UP: next map' if game.room_clear else 'Locked', centered=True, color=GOLD)
        elif game.checkpoint.can_activate(game.player):
            self.text(640, 565, '체크포인트 활성' if game.checkpoint.active else '↑ 체크포인트 활성화',
                      'Checkpoint active' if game.checkpoint.active else 'UP: activate checkpoint', centered=True)
        elif game.at_boss_gate and not game.boss_active:
            self.text(640, 565, '↑ 보스 도전', 'UP: challenge boss', centered=True)

    def draw(self, game):
        p2d.draw_rectangle(0, 0, 1279, 99, 13, 15, 26, filled=True)
        p2d.draw_rectangle(0, 98, 1279, 99, 87, 73, 66, filled=True)
        self.draw_player(game.player)
        self.draw_abilities()
        self.draw_boss(game)
        self.draw_location(game)
        self.draw_notifications(game)
        self.text(775, 71, '방향키 이동  C 점프  ↓+C 하강', 'Arrows move / C jump / Down+C drop', font=self.small)
        self.text(775, 50, 'X 공격  Z 대시  Space 무기 전환', 'X attack / Z dash / Space switch', font=self.small)
        self.text(775, 29, '↑ 상호작용  R 재시작  F2 판정  Esc 종료',
                  'Up interact / R retry / F2 boxes / Esc quit', color=GOLD, font=self.small)
