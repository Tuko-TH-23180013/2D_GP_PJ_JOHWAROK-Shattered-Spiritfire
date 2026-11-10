"""조화록: 실행 루프와 1단계 이동 연습장."""

import ctypes
from dataclasses import dataclass, field
from time import perf_counter

from pico2d import pico2d as p2d
import sdl2
from player import Player
from world import World

from settings import MAX_DT, TARGET_FPS, WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH


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

    def update(self, dt):
        self.elapsed += dt
        direction = (int(sdl2.SDLK_RIGHT in self.inputs.held)
                     - int(sdl2.SDLK_LEFT in self.inputs.held))
        self.player.update(dt, direction, sdl2.SDLK_c in self.inputs.pressed,
                           self.world)

    def draw(self):
        # 내부 좌표는 왼쪽 아래 원점, 픽셀 단위. 이후 속도는 픽셀/초.
        p2d.clear_canvas()
        p2d.draw_rectangle(0, 0, WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1,
                          24, 28, 36, filled=True)
        for solid in self.world.solids:
            p2d.draw_rectangle(solid.left, solid.bottom, solid.right, solid.top,
                              95, 110, 125, filled=True)
        player = self.player
        color = (90, 160, 240) if player.grounded else (100, 230, 160)
        # 외형은 충돌 상자보다 좌우 6px, 위쪽 8px 크다.
        p2d.draw_rectangle(player.x - 6, player.y, player.x + player.width + 6,
                          player.y + player.height + 8, *color, filled=True)
        p2d.draw_rectangle(player.x, player.y, player.x + player.width,
                          player.y + player.height, 255, 215, 90)
        eye_x = player.x + (player.width - 7 if player.facing > 0 else 7)
        p2d.draw_rectangle(eye_x - 2, player.y + 48, eye_x + 2,
                          player.y + 53, 24, 28, 36, filled=True)
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
                         " | C: double jump | Esc: quit")
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
