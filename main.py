"""조화록: 장승마을 진행·전투·체크포인트 실행 루프."""

import ctypes
from dataclasses import dataclass, field
from time import perf_counter

from pico2d import pico2d as p2d
import sdl2
from player import Player
from combat_system import CombatSystem
from training_dummy import TrainingDummy
from stage import VillageStage
from camera import Camera
from checkpoint import Checkpoint
from boss import Boss
from sprite_animation import HeroAnimation
from sprite_renderer import DemoSprites
from weapon_data import WEAPONS

from settings import MAX_DT, TARGET_FPS, WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH, PHYSICS_STEP


@dataclass
class InputState:
    held: set[int] = field(default_factory=set)
    pressed: set[int] = field(default_factory=set)
    released: set[int] = field(default_factory=set)
    quit_requested: bool = False

    def collect(self, events):
        self.pressed.clear()
        self.released.clear()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                self.quit_requested = True
            elif event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                if not event.key.repeat and key not in self.held:
                    self.pressed.add(key)
                self.held.add(key)
                if key == sdl2.SDLK_ESCAPE:
                    self.quit_requested = True
            elif event.type == sdl2.SDL_KEYUP:
                key = event.key.keysym.sym
                self.held.discard(key)
                self.released.add(key)
            elif (event.type == sdl2.SDL_WINDOWEVENT
                  and event.window.event == sdl2.SDL_WINDOWEVENT_FOCUS_LOST):
                self.released.update(self.held)
                self.held.clear()


def poll_events():
    # Pico2D 1.5.1의 get_events는 포커스 이벤트를 버리므로 SDL에서 수집한다.
    event = sdl2.SDL_Event()
    while sdl2.SDL_PollEvent(ctypes.byref(event)):
        yield event


class Game:
    def __init__(self):
        self.inputs = InputState()
        self.elapsed = 0.0
        self.stage = VillageStage()
        self.world = self.stage.create_world()
        self.camera = Camera(self.stage.width)
        self.checkpoint = Checkpoint(self.stage.checkpoint_spawn)
        self.at_boss_gate = False
        self.player = Player()
        self.combat = CombatSystem()
        self.dummy = TrainingDummy()
        self.enemies = self.stage.create_enemies()
        self.boss = None
        self.boss_active = False
        self.victory = False
        self.hero_animation = HeroAnimation()
        self.visuals = None  # 테스트는 창 없이 구성 가능. 첫 draw에서만 로드.
        self.show_hitboxes = False

    def release_assets(self):
        self.visuals = None

    def start_boss(self):
        if not self.at_boss_gate or self.boss_active or self.player.hp <= 0:
            return False
        hp, weapon = self.player.hp, self.player.weapon
        self.player = Player(*self.stage.arena_spawn, weapon=weapon)
        self.hero_animation = HeroAnimation()
        self.player.hp = hp
        self.boss = Boss()
        self.boss_active = True
        self.world.solids.append(self.stage.arena_barrier)
        self.inputs.held.clear()
        self.inputs.pressed.clear()
        self.camera.follow(self.player)
        return True

    def restart(self):
        active = self.checkpoint.active
        visuals, hitboxes = self.visuals, self.show_hitboxes
        self.__init__()
        self.visuals, self.show_hitboxes = visuals, hitboxes
        if active:
            self.checkpoint.active = True
            self.player.x, self.player.y = self.checkpoint.spawn
        self.camera.follow(self.player)

    def update(self, dt):
        if sdl2.SDLK_F2 in self.inputs.pressed:
            self.show_hitboxes = not self.show_hitboxes
        if sdl2.SDLK_r in self.inputs.pressed:
            self.restart()
            return
        if self.player.hp <= 0 or self.victory:
            return
        self.elapsed += dt
        previous_x = self.player.x
        direction = (int(sdl2.SDLK_RIGHT in self.inputs.held)
                     - int(sdl2.SDLK_LEFT in self.inputs.held))
        self.combat.begin_frame()
        remaining = dt
        first = True
        while remaining > 1e-9:
            step = min(remaining, PHYSICS_STEP)
            remaining -= step
            self.combat.update_target(self.player, step)
            self.player.update(step, direction, first and sdl2.SDLK_c in self.inputs.pressed,
                               self.world, down_held=sdl2.SDLK_DOWN in self.inputs.held,
                               dash_pressed=first and sdl2.SDLK_z in self.inputs.pressed,
                               attack_pressed=first and sdl2.SDLK_x in self.inputs.pressed,
                               switch_pressed=first and sdl2.SDLK_SPACE in self.inputs.pressed)
            self.combat.update_target(self.dummy, step)
            for enemy in self.enemies:
                self.combat.update_target(enemy, step)
                enemy.update(step, self.player, self.world)
            if self.boss_active:
                self.combat.update_target(self.boss, step)
                self.boss.update(step, self.player, self.world)
            if self.player.attack is not None:
                targets = [self.dummy, *self.enemies]
                if self.boss_active:
                    targets.append(self.boss)
                self.combat.resolve([self.player.attack], targets)
            if self.boss_active and self.boss.hp <= 0:
                self.victory = True
                self.player.attack = None
                self.player.attack_queued = self.player.switch_queued = False
                for enemy in self.enemies:
                    enemy.attack = None
                break
            for enemy in self.enemies:
                if enemy.attack is not None:
                    self.combat.resolve([enemy.attack], [self.player])
            if self.boss_active and self.boss.attack is not None:
                self.combat.resolve([self.boss.attack], [self.player])
            # 순회가 끝난 뒤 사망 객체를 제거한다.
            self.enemies = [enemy for enemy in self.enemies if enemy.hp > 0]
            if self.player.hp <= 0:
                for enemy in self.enemies:
                    enemy.attack = None
                    enemy.state = "IDLE"
                if self.boss is not None:
                    self.boss.attack = None
                break
            first = False
        self.camera.follow(self.player)
        self.hero_animation.update(self.player, dt, previous_x)
        self.at_boss_gate = (self.player.hp > 0
                            and self.player.x + self.player.width >= self.stage.boss_entrance.left
                            and self.player.x <= self.stage.boss_entrance.right
                            and self.player.y < self.stage.boss_entrance.top)
        if sdl2.SDLK_UP in self.inputs.pressed:
            self.checkpoint.activate(self.player)
            self.start_boss()

    def draw(self):
        if self.visuals is None:
            self.visuals = DemoSprites()
        def draw_world(left, bottom, right, top, *color, **kwargs):
            p2d.draw_rectangle(*self.camera.screen_rect(left, bottom, right, top),
                              *color, **kwargs)

        # 내부 좌표는 왼쪽 아래 원점, 픽셀 단위. 이후 속도는 픽셀/초.
        p2d.clear_canvas()
        p2d.draw_rectangle(0, 0, WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1,
                          24, 28, 36, filled=True)
        self.visuals.draw_background(self.camera)
        for solid in self.world.solids:
            color = (110, 170, 140) if solid.one_way else (95, 110, 125)
            draw_world(solid.left, solid.bottom, solid.right, solid.top,
                              *color, filled=True)
        player = self.player
        # 지역 표식은 충돌하지 않는 임시 장승/문 형태다.
        for start, _ in self.stage.regions[1:]:
            draw_world(start, 100, start + 20, 195, 100, 70, 45, filled=True)
            draw_world(start - 12, 165, start + 32, 175, 160, 130, 70, filled=True)
        gate = self.stage.boss_entrance
        draw_world(gate.left, gate.bottom, gate.right, gate.top, 170, 95, 180)
        cx, cy = self.checkpoint.spawn
        cp_color = (90, 245, 190) if self.checkpoint.active else (80, 130, 190)
        draw_world(cx - 16, cy, cx + 16, cy + 110, *cp_color, filled=True)
        draw_world(cx - 32, cy + 75, cx + 32, cy + 90, *cp_color, filled=True)
        if self.checkpoint.can_activate(player) and not self.checkpoint.active:
            draw_world(cx - 4, cy + 125, cx + 4, cy + 150, 240, 240, 170, filled=True)
            draw_world(cx - 12, cy + 138, cx + 12, cy + 145, 240, 240, 170, filled=True)
        p2d.draw_rectangle(25, 635, 225, 653, 70, 40, 45, filled=True)
        if player.hp > 0:
            p2d.draw_rectangle(25, 635, 25 + 200 * player.hp / player.max_hp,
                              653, 230, 80, 100, filled=True)
        visible_enemies = self.enemies + ([self.boss] if self.boss_active and self.boss.hp > 0 else [])
        for enemy in visible_enemies:
            color = {"STARTUP": (240, 210, 65), "ACTIVE": (245, 75, 60),
                     "RECOVERY": (125, 90, 105), "STAGGER": (190, 90, 235)}.get(
                         enemy.state, (190, 90, 70))
            if enemy.hit_flash > 0:
                color = (255, 230, 220)
            if isinstance(enemy, Boss):
                if enemy.state in ("DOWN", "WAKE"):
                    color = (100, 100, 210) if enemy.state == "DOWN" else (150, 130, 210)
                elif enemy.state == "STARTUP":
                    color = (240, 200, 65) if enemy.pattern == "SWING" else (230, 100, 220)
            draw_world(enemy.x, enemy.y, enemy.x + enemy.width,
                              enemy.y + enemy.height, *color, filled=True)
            draw_world(enemy.x, enemy.y + enemy.height + 9,
                              enemy.x + enemy.width * enemy.hp / enemy.max_hp,
                              enemy.y + enemy.height + 15, 240, 65, 65, filled=True)
            if enemy.stagger > 0:
                draw_world(enemy.x, enemy.y + enemy.height + 19,
                                  enemy.x + enemy.width * enemy.stagger / enemy.stagger_limit,
                                  enemy.y + enemy.height + 24, 180, 80, 230, filled=True)
            if enemy.attack is not None and enemy.attack.phase == "ACTIVE":
                box = enemy.attack.bounds
                draw_world(box.left, box.bottom, box.right, box.top, 255, 70, 70)
        weapon_color = (110, 190, 250) if player.weapon == "basic" else (215, 145, 65)
        p2d.draw_rectangle(130, 675, 155 if player.weapon == "basic" else 180,
                          695, *weapon_color, filled=True)
        dummy = self.dummy
        self.visuals.draw_dummy(dummy, self.camera)
        draw_world(dummy.x - 10, 205, dummy.x + 70, 213, 70, 40, 40, filled=True)
        if dummy.hp > 0:
            draw_world(dummy.x - 10, 205,
                              dummy.x - 10 + 80 * dummy.hp / dummy.max_hp,
                              213, 220, 85, 85, filled=True)
        if dummy.stagger > 0:
            draw_world(dummy.x - 10, 192,
                              dummy.x - 10 + 80 * dummy.stagger / dummy.stagger_limit,
                              198, 190, 110, 245, filled=True)
        if player.attack is not None and player.attack.phase == "ACTIVE":
            box = player.attack.bounds
            draw_world(box.left, box.bottom, box.right, box.top, 255, 130, 50)
        for hazard in self.world.hazards:
            draw_world(hazard.left, hazard.bottom, hazard.right, hazard.top,
                              180, 55, 65, filled=True)
        for index in range(2):
            color = (80, 220, 240) if index < player.dash_charges else (65, 70, 80)
            p2d.draw_rectangle(25 + index * 45, 675, 60 + index * 45, 695,
                              *color, filled=True)
        color = (90, 160, 240) if player.grounded else (100, 230, 160)
        if player.hit_flash > 0:
            color = (255, 85, 95)
        elif player.invulnerable:
            color = (245, 245, 255)
        elif player.hazard_exposed:
            color = (255, 80, 90)
        elif player.dash_remaining > 1e-9:
            color = (255, 180, 70)
        if player.switch_remaining > 0:
            # 에셋 도입 전 사각형 불꽃으로 표시하는 임시 도깨비불 연출.
            for index in range(5):
                flame_x = player.x - 12 + index * 15
                rise = ((self.elapsed * 120 + index * 11) % 30)
                draw_world(flame_x, player.y - 4 + rise,
                                  flame_x + 8, player.y + 30 + rise,
                                  50, 170, 250, filled=True)
                draw_world(flame_x + 2, player.y + rise,
                                  flame_x + 6, player.y + 18 + rise,
                                  170, 250, 250, filled=True)
        self.visuals.draw_hero(player, self.hero_animation, self.camera)
        # 데모 포즈와 독립적인 기존 충돌/무적 상태를 확인할 수 있다.
        draw_world(player.x, player.y - 3, player.x + player.width,
                   player.y - 1, *color, filled=True)
        if self.show_hitboxes:
            draw_world(player.x, player.y, player.x + player.width,
                       player.y + player.height, 255, 215, 90)
        if player.attack is not None:
            phase_color = {"STARTUP": (245, 220, 70), "ACTIVE": (255, 130, 50),
                           "RECOVERY": (140, 130, 180)}[player.attack.phase]
            draw_world(player.x, player.y + player.height + 14,
                              player.x + player.width, player.y + player.height + 20,
                              *phase_color, filled=True)
        if self.boss_active:
            p2d.draw_rectangle(350, 665, 1000, 690, 70, 35, 45, filled=True)
            if self.boss.hp > 0:
                p2d.draw_rectangle(350, 665, 350 + 650 * self.boss.hp / self.boss.max_hp,
                                  690, 210, 55, 85, filled=True)
            if self.boss.stagger > 0:
                p2d.draw_rectangle(350, 650, 350 + 650 * self.boss.stagger / self.boss.stagger_limit,
                                  657, 140, 100, 240, filled=True)
        if self.victory:
            p2d.draw_rectangle(410, 290, 870, 430, 20, 65, 50, filled=True)
            p2d.draw_rectangle(410, 290, 870, 430, 100, 245, 180)
        elif player.hp <= 0:
            # 제목 표시줄에 재시작 안내, 화면에는 사망 상태를 나타내는 붉은 패널.
            p2d.draw_rectangle(450, 300, 830, 420, 65, 20, 30, filled=True)
            p2d.draw_rectangle(450, 300, 830, 420, 230, 70, 90)
            p2d.draw_rectangle(628, 325, 652, 395, 230, 70, 90, filled=True)
            p2d.draw_rectangle(605, 348, 675, 372, 230, 70, 90, filled=True)
        self.visuals.draw_labels(self)
        p2d.update_canvas()


def run(frame_hook=None):
    """frame_hook은 실제 SDL 이벤트를 주입하는 실행 검증용이다."""
    p2d.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT, sync=True)
    try:
        if not p2d.window or not p2d.renderer:
            raise RuntimeError("SDL 창 또는 렌더러를 생성하지 못했습니다.")
        # 월드 좌표는 유지하고, 모니터 작업 영역에 맞춰 출력만 확대한다.
        if sdl2.SDL_RenderSetLogicalSize(p2d.renderer, WINDOW_WIDTH, WINDOW_HEIGHT) != 0:
            raise RuntimeError("논리 화면 크기를 설정하지 못했습니다.")
        sdl2.SDL_SetWindowResizable(p2d.window, sdl2.SDL_TRUE)
        sdl2.SDL_MaximizeWindow(p2d.window)
        game = Game()
        previous = perf_counter()
        fps_elapsed = 0.0
        fps_frames = 0
        frames = 0
        while not game.inputs.quit_requested:
            start = perf_counter()
            raw_dt = max(0.0, start - previous)
            previous = start
            dt = min(raw_dt, MAX_DT)
            if frame_hook is not None:
                frame_hook(frames)
            game.inputs.collect(poll_events())
            if game.inputs.quit_requested:
                break
            game.update(dt)
            game.draw()
            frames += 1
            fps_frames += 1
            fps_elapsed += raw_dt
            if fps_elapsed >= 0.25 or frames == 1:
                fps = fps_frames / fps_elapsed if fps_elapsed else 0.0
                title = (f"{WINDOW_TITLE} | {game.stage.region_at(game.player.x)} | {fps:.0f} FPS | Left/Right: move"
                         " | C: jump | Down+C: drop | Z: dash | X: attack | Space: switch | R: restart | Esc: quit"
                         f" | Weapon: {WEAPONS[game.player.weapon].name}"
                         f"{' (queued)' if game.player.switch_queued else ''}"
                         f" | Charges: {game.player.dash_charges}/2"
                         f" | Recharge: {game.player.recharge_remaining:.1f}s"
                         f" | Dummy HP: {game.dummy.hp}"
                         f" | Player HP: {game.player.hp}"
                         f" | Hazard hits: {game.player.hazard_hits}"
                         f" | Attack: {game.player.attack.data.name + ' ' + game.player.attack.phase if game.player.attack else 'Idle'}")
                if game.victory:
                    title = "JOHWAROK - VICTORY! Old Dokkaebi defeated | R: retry | Esc: quit"
                elif game.player.hp <= 0:
                    title = "JOHWAROK - YOU DIED | Press R to restart | Esc: quit"
                elif game.checkpoint.can_activate(game.player):
                    title = ("JOHWAROK - Checkpoint ACTIVE | R: respawn here" if game.checkpoint.active
                             else "JOHWAROK - Press UP to activate checkpoint | R: restart")
                elif game.at_boss_gate and not game.boss_active:
                    title = "JOHWAROK - Press UP to challenge Old Dokkaebi | R: restart"
                elif game.boss_active:
                    title = (f"JOHWAROK - Old Dokkaebi HP {game.boss.hp}/{game.boss.max_hp}"
                             f" | {game.boss.pattern}: {game.boss.state}"
                             f" | Player HP {game.player.hp} | X: attack | C: jump | Z: dash | Space: switch | R: retry")
                sdl2.SDL_SetWindowTitle(p2d.window, title.encode("utf-8"))
                fps_elapsed = 0.0
                fps_frames = 0
            remaining = 1.0 / TARGET_FPS - (perf_counter() - start)
            if remaining > 0:
                p2d.delay(remaining)
        return frames
    finally:
        if 'game' in locals():
            game.release_assets()
        p2d.close_canvas()


if __name__ == "__main__":
    run()
