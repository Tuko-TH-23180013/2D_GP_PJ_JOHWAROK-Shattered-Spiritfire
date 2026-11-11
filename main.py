"""조화록: 실행 루프와 4단계 무기 전환 전투 연습장."""

import ctypes
from dataclasses import dataclass, field
from time import perf_counter

from pico2d import pico2d as p2d
import sdl2
from player import Player
from world import World
from combat_system import CombatSystem
from training_dummy import TrainingDummy
from enemy import Enemy
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
        self.world = World()
        self.player = Player()
        self.combat = CombatSystem()
        self.dummy = TrainingDummy()
        self.enemies = [Enemy()]

    def update(self, dt):
        self.elapsed += dt
        direction = (int(sdl2.SDLK_RIGHT in self.inputs.held)
                     - int(sdl2.SDLK_LEFT in self.inputs.held))
        if sdl2.SDLK_r in self.inputs.pressed:
            self.dummy = TrainingDummy()
            self.player.attack = None
            self.player.attack_queued = False
            self.player.switch_queued = False
            self.player.switch_remaining = 0.0
            self.player.switch_invulnerability = 0.0
        self.combat.begin_frame()
        remaining = dt
        first = True
        while remaining > 1e-9:
            step = min(remaining, PHYSICS_STEP)
            remaining -= step
            self.player.update(step, direction, first and sdl2.SDLK_c in self.inputs.pressed,
                               self.world, down_held=sdl2.SDLK_DOWN in self.inputs.held,
                               dash_pressed=first and sdl2.SDLK_z in self.inputs.pressed,
                               attack_pressed=first and sdl2.SDLK_x in self.inputs.pressed,
                               switch_pressed=first and sdl2.SDLK_SPACE in self.inputs.pressed)
            self.combat.update_target(self.dummy, step)
            for enemy in self.enemies:
                self.combat.update_target(enemy, step)
                enemy.update(step, self.player, self.world)
            if self.player.attack is not None:
                self.combat.resolve([self.player.attack], [self.dummy])
            first = False

    def draw(self):
        # 내부 좌표는 왼쪽 아래 원점, 픽셀 단위. 이후 속도는 픽셀/초.
        p2d.clear_canvas()
        p2d.draw_rectangle(0, 0, WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1,
                          24, 28, 36, filled=True)
        for solid in self.world.solids:
            color = (110, 170, 140) if solid.one_way else (95, 110, 125)
            p2d.draw_rectangle(solid.left, solid.bottom, solid.right, solid.top,
                              *color, filled=True)
        player = self.player
        for enemy in self.enemies:
            color = {"STARTUP": (240, 210, 65), "ACTIVE": (245, 75, 60),
                     "RECOVERY": (125, 90, 105), "STAGGER": (190, 90, 235)}.get(
                         enemy.state, (190, 90, 70))
            p2d.draw_rectangle(enemy.x, enemy.y, enemy.x + enemy.width,
                              enemy.y + enemy.height, *color, filled=True)
            p2d.draw_rectangle(enemy.x, enemy.y + enemy.height + 9,
                              enemy.x + enemy.width * enemy.hp / enemy.max_hp,
                              enemy.y + enemy.height + 15, 240, 65, 65, filled=True)
            if enemy.attack is not None and enemy.attack.phase == "ACTIVE":
                box = enemy.attack.bounds
                p2d.draw_rectangle(box.left, box.bottom, box.right, box.top, 255, 70, 70)
        weapon_color = (110, 190, 250) if player.weapon == "basic" else (215, 145, 65)
        p2d.draw_rectangle(130, 675, 155 if player.weapon == "basic" else 180,
                          695, *weapon_color, filled=True)
        dummy = self.dummy
        if dummy.hp > 0:
            color = ((255, 245, 220) if dummy.hit_flash > 0 else
                     (180, 100, 220) if dummy.stagger_remaining > 0 else (170, 125, 75))
            p2d.draw_rectangle(dummy.x, dummy.y, dummy.x + dummy.width,
                              dummy.y + dummy.height, *color, filled=True)
        p2d.draw_rectangle(dummy.x - 10, 205, dummy.x + 70, 213, 70, 40, 40, filled=True)
        if dummy.hp > 0:
            p2d.draw_rectangle(dummy.x - 10, 205,
                              dummy.x - 10 + 80 * dummy.hp / dummy.max_hp,
                              213, 220, 85, 85, filled=True)
        if dummy.stagger > 0:
            p2d.draw_rectangle(dummy.x - 10, 192,
                              dummy.x - 10 + 80 * dummy.stagger / dummy.stagger_limit,
                              198, 190, 110, 245, filled=True)
        if player.attack is not None and player.attack.phase == "ACTIVE":
            box = player.attack.bounds
            p2d.draw_rectangle(box.left, box.bottom, box.right, box.top, 255, 130, 50)
        for hazard in self.world.hazards:
            p2d.draw_rectangle(hazard.left, hazard.bottom, hazard.right, hazard.top,
                              180, 55, 65, filled=True)
        for index in range(2):
            color = (80, 220, 240) if index < player.dash_charges else (65, 70, 80)
            p2d.draw_rectangle(25 + index * 45, 675, 60 + index * 45, 695,
                              *color, filled=True)
        color = (90, 160, 240) if player.grounded else (100, 230, 160)
        if player.invulnerable:
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
                p2d.draw_rectangle(flame_x, player.y - 4 + rise,
                                  flame_x + 8, player.y + 30 + rise,
                                  50, 170, 250, filled=True)
                p2d.draw_rectangle(flame_x + 2, player.y + rise,
                                  flame_x + 6, player.y + 18 + rise,
                                  170, 250, 250, filled=True)
        # 외형은 충돌 상자보다 좌우 6px, 위쪽 8px 크다.
        p2d.draw_rectangle(player.x - 6, player.y, player.x + player.width + 6,
                          player.y + player.height + 8, *color, filled=True)
        p2d.draw_rectangle(player.x, player.y, player.x + player.width,
                          player.y + player.height, 255, 215, 90)
        eye_x = player.x + (player.width - 7 if player.facing > 0 else 7)
        p2d.draw_rectangle(eye_x - 2, player.y + 48, eye_x + 2,
                          player.y + 53, 24, 28, 36, filled=True)
        if player.attack is not None:
            phase_color = {"STARTUP": (245, 220, 70), "ACTIVE": (255, 130, 50),
                           "RECOVERY": (140, 130, 180)}[player.attack.phase]
            p2d.draw_rectangle(player.x, player.y + player.height + 14,
                              player.x + player.width, player.y + player.height + 20,
                              *phase_color, filled=True)
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
                title = (f"{WINDOW_TITLE} | {fps:.0f} FPS | Left/Right: move"
                         " | C: jump | Down+C: drop | Z: dash | X: attack | Space: switch | R: dummy | Esc: quit"
                         f" | Weapon: {WEAPONS[game.player.weapon].name}"
                         f"{' (queued)' if game.player.switch_queued else ''}"
                         f" | Charges: {game.player.dash_charges}/2"
                         f" | Recharge: {game.player.recharge_remaining:.1f}s"
                         f" | Dummy HP: {game.dummy.hp}"
                         f" | Hazard hits: {game.player.hazard_hits}"
                         f" | Attack: {game.player.attack.data.name + ' ' + game.player.attack.phase if game.player.attack else 'Idle'}")
                sdl2.SDL_SetWindowTitle(p2d.window, title.encode("utf-8"))
                fps_elapsed = 0.0
                fps_frames = 0
            remaining = 1.0 / TARGET_FPS - (perf_counter() - start)
            if remaining > 0:
                p2d.delay(remaining)
        return frames
    finally:
        p2d.close_canvas()


if __name__ == "__main__":
    run()
