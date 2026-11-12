"""실제 창에서 적 공격·플레이어 사망·R 재시작·적 처치를 검증한다."""
import ctypes
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sdl2
from pico2d import pico2d as p2d
from main import Game, poll_events
from settings import WINDOW_WIDTH, WINDOW_HEIGHT


def main():
    p2d.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT, sync=True)
    try:
        if not p2d.window or not p2d.renderer:
            raise RuntimeError('창 생성 실패')
        game = Game()
        game.player.x, game.player.hp = 820, 15
        for _ in range(90):
            game.inputs.collect(poll_events())
            game.update(1 / 60)
            game.draw()
        assert game.player.hp == 0
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_KEYDOWN
        event.key.keysym.sym = sdl2.SDLK_r
        assert sdl2.SDL_PushEvent(ctypes.byref(event)) == 1
        game.inputs.collect(poll_events())
        game.update(1 / 60)
        game.draw()
        assert game.player.hp == 100 and game.player.x == 120
        game.player.x = 820
        game.enemies[0].hp = 10
        event.key.keysym.sym = sdl2.SDLK_x
        assert sdl2.SDL_PushEvent(ctypes.byref(event)) == 1
        for _ in range(60):
            game.inputs.collect(poll_events())
            game.update(1 / 60)
            game.draw()
        assert not game.enemies and game.player.hp == 100
        print('PASS: enemy attack, death drawing, SDL R restart, SDL X kill, cleanup')
    finally:
        if 'game' in locals():
            game.release_assets()
        p2d.close_canvas()


if __name__ == '__main__':
    main()
