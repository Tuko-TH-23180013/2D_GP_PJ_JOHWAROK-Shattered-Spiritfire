"""실제 창에서 스크롤·체크포인트 입력·재시작·보스 입구 표시를 검사한다."""
import ctypes
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sdl2
from pico2d import pico2d as p2d
from main import Game, poll_events
from settings import WINDOW_WIDTH, WINDOW_HEIGHT


def key(game, code):
    event = sdl2.SDL_Event()
    event.type = sdl2.SDL_KEYDOWN
    event.key.keysym.sym = code
    assert sdl2.SDL_PushEvent(ctypes.byref(event)) == 1
    game.inputs.collect(poll_events())
    game.update(1 / 60)


def main():
    p2d.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT, sync=True)
    try:
        if not p2d.window or not p2d.renderer:
            raise RuntimeError('창 생성 실패')
        game = Game()
        # 위치 지정은 화면 범위 검사 용도. 전체 이동 경로는 unittest로 검사한다.
        for x in (120, 1500, 2500, 3100):
            game.player.x = x
            for _ in range(12):
                game.inputs.collect(poll_events())
                game.update(1 / 60)
                game.draw()
        assert game.at_boss_gate
        game.player.x = 2500
        key(game, sdl2.SDLK_UP)
        assert game.checkpoint.active
        game.player.hp = 0
        game.player.on_combat_hit()
        game.draw()
        key(game, sdl2.SDLK_r)
        game.draw()
        assert game.player.x == 2500 and game.player.hp == 100
        assert game.camera.x > 0
        print('PASS: scrolled drawing, gate, SDL UP checkpoint, death, SDL R respawn')
    finally:
        p2d.close_canvas()


if __name__ == '__main__':
    main()
