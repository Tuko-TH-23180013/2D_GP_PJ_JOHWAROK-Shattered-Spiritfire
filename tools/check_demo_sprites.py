"""실제 창에서 데모 25프레임 좌우 반전과 리소스 재사용 검사."""
from pathlib import Path
import ctypes
import tempfile
import sys
import sdl2
from sdl2.sdlimage import IMG_SavePNG

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pico2d import pico2d as p2d
from main import Game
from settings import WINDOW_WIDTH, WINDOW_HEIGHT


def main():
    p2d.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT, sync=True)
    game = None
    try:
        game = Game()
        game.player.x = 350
        for direction in (1, -1):
            game.player.facing = direction
            for frame in range(25):
                game.hero_animation.frame = frame
                game.draw()
                p2d.get_events()
        resource = game.visuals
        game.restart()
        game.draw()
        assert game.visuals is resource
        del resource
        # SDL가 그린 실제 프레임을 임시 PNG로 저장해 시각 검토한다.
        game.player.x = 350
        game.hero_animation.frame = 17
        present = p2d.update_canvas
        p2d.update_canvas = lambda: None
        try:
            game.draw()
            surface = sdl2.SDL_CreateRGBSurfaceWithFormat(0, WINDOW_WIDTH, WINDOW_HEIGHT,
                                                         32, sdl2.SDL_PIXELFORMAT_ARGB8888)
            if not surface:
                raise RuntimeError('화면 캡처 메모리 생성 실패')
            try:
                assert sdl2.SDL_RenderReadPixels(p2d.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888,
                                               surface.contents.pixels, surface.contents.pitch) == 0
                capture = Path(tempfile.gettempdir()) / 'johwarok-demo-sprites.png'
                assert IMG_SavePNG(surface, str(capture).encode('utf-8')) == 0
                print(f'CAPTURE: {capture}')
            finally:
                sdl2.SDL_FreeSurface(surface)
        finally:
            p2d.update_canvas = present
        present()
        print('PASS: 25 demo frames x 2 directions, restart resource reuse')
    finally:
        if game is not None:
            game.release_assets()
        p2d.close_canvas()


if __name__ == '__main__':
    main()
