"""실제 창을 잠깐 열고 Esc/종료 이벤트 두 경로를 검사한다."""

import ctypes
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sdl2
from main import run


def check(exit_type):
    def inject(frame):
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
