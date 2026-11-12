"""실제 창의 보스 입장/다운/기상/사망/재도전/승리 그리기 검사.

경계 상태를 빠르게 확인하기 위해 테스트에서 HP·스태거·위치를 지정한다.
"""
import ctypes
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sdl2
from pico2d import pico2d as p2d
from main import Game, poll_events
from settings import WINDOW_WIDTH, WINDOW_HEIGHT


def press(game, code):
    event = sdl2.SDL_Event()
    event.type = sdl2.SDL_KEYDOWN
    event.key.keysym.sym = code
    assert sdl2.SDL_PushEvent(ctypes.byref(event)) == 1
    game.inputs.collect(poll_events())
    game.update(1 / 60)
    game.inputs.held.clear()
    game.inputs.pressed.clear()


def frames(game, count):
    for _ in range(count):
        game.inputs.collect(poll_events())
        game.update(1 / 60)
        game.draw()


def main():
    p2d.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT, sync=True)
    try:
        if not p2d.window or not p2d.renderer:
            raise RuntimeError('창 생성 실패')
        game = Game()
        game.checkpoint.active = True
        game.player.x = 3100
        press(game, sdl2.SDLK_UP)
        assert game.boss_active
        game.player.x = game.boss.x - 70
        game.boss.stagger = 105
        press(game, sdl2.SDLK_x)
        frames(game, 10)
        assert game.boss.state == 'DOWN'
        frames(game, 120)
        assert game.boss.state == 'WAKE'
        frames(game, 45)
        game.player.hp = 1
        frames(game, 150)
        assert game.player.hp == 0
        press(game, sdl2.SDLK_r)
        assert game.player.x == 2500
        game.player.x = 3100
        press(game, sdl2.SDLK_UP)
        game.player.x = game.boss.x - 70
        game.boss.hp = 10
        press(game, sdl2.SDLK_x)
        frames(game, 30)
        assert game.victory and game.boss.hp == 0
        print('PASS: SDL entry, DOWN/WAKE drawing, death, checkpoint retry, victory drawing')
    finally:
        if 'game' in locals():
            game.release_assets()
        p2d.close_canvas()


if __name__ == '__main__':
    main()
