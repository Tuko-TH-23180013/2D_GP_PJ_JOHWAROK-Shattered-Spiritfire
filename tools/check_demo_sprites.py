"""실제 창에서 데모 25프레임 좌우 반전과 리소스 재사용 검사."""
from pathlib import Path
import sys

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
        print('PASS: 25 demo frames x 2 directions, restart resource reuse')
    finally:
        if game is not None:
            game.release_assets()
        p2d.close_canvas()


if __name__ == '__main__':
    main()
