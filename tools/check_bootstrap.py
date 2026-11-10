"""실제 창을 잠깐 열고 Esc/종료 이벤트 두 경로를 검사한다."""

import ctypes
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sdl2
from main import run
from pico2d import pico2d as p2d
from settings import WINDOW_WIDTH, WINDOW_HEIGHT


def check(exit_type):
    def inject(frame):
        if frame in (12, 13):
            event = sdl2.SDL_Event()
            event.type = sdl2.SDL_KEYDOWN if frame == 12 else sdl2.SDL_KEYUP
            event.key.keysym.sym = sdl2.SDLK_x
            if sdl2.SDL_PushEvent(ctypes.byref(event)) != 1:
                raise RuntimeError("공격 입력 주입 실패")
        if frame == 10:
            width, height = ctypes.c_int(), ctypes.c_int()
            sdl2.SDL_GetWindowSize(p2d.window, ctypes.byref(width), ctypes.byref(height))
            assert sdl2.SDL_GetWindowFlags(p2d.window) & sdl2.SDL_WINDOW_MAXIMIZED
            print(f"Maximized window: {width.value}x{height.value}")
            sdl2.SDL_RenderGetLogicalSize(p2d.renderer, ctypes.byref(width), ctypes.byref(height))
            assert (width.value, height.value) == (WINDOW_WIDTH, WINDOW_HEIGHT)
        if frame > 120:
            raise AssertionError("종료 이벤트 처리 실패")
        if frame == 30:
            event = sdl2.SDL_Event()
            event.type = exit_type
            if exit_type == sdl2.SDL_KEYDOWN:
                event.key.keysym.sym = sdl2.SDLK_ESCAPE
            if sdl2.SDL_PushEvent(ctypes.byref(event)) != 1:
                raise RuntimeError("SDL 이벤트 주입 실패")

    frames = run(frame_hook=inject)
    assert frames == 30, f"예상하지 못한 종료 시점: {frames}"
    print(f"PASS: {exit_type=}, {frames=}")


if __name__ == "__main__":
    check(sdl2.SDL_KEYDOWN)
    check(sdl2.SDL_QUIT)
