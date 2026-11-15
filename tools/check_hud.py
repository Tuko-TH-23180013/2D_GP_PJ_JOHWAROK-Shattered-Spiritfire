"""실제 SDL에서 데모 HUD 상태·재시작 캐시 및 논리 화면 확대를 검사한다."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sdl2
from pico2d import pico2d as p2d
from main import MapGame
from tools.check_monster_maps import capture
from settings import DASH_RECHARGE


def main():
    p2d.open_canvas(1280, 720, sync=True)
    game = MapGame()
    present = p2d.update_canvas
    try:
        p2d.update_canvas = lambda: None
        game.player.x = 450
        for hp, charges, weapon in ((100, 2, 'basic'), (37, 1, 'giant'), (0, 0, 'giant')):
            game.player.hp, game.player.dash_charges, game.player.weapon = hp, charges, weapon
            game.player.recharge_remaining = DASH_RECHARGE / 2
            game.player.switch_queued = hp == 37
            game.draw()
            capture(f'johwarok-hud-player-{hp}.png')
            present()
            p2d.get_events()
        resource = game.visuals.hud
        game.restart()
        game.draw()
        assert resource is game.visuals.hud
        for index in (2, 6):
            game.enter_room(index)
            game.boss.hp //= 2
            game.boss.stagger = game.boss.stagger_limit * .6
            game.draw()
            capture(f'johwarok-hud-boss-{index}.png')
            present()
        game.enter_room(3)
        game.draw()
        capture('johwarok-hud-save.png')
        present()
        assert sdl2.SDL_RenderSetLogicalSize(p2d.renderer, 1280, 720) == 0
        sdl2.SDL_SetWindowResizable(p2d.window, sdl2.SDL_TRUE)
        sdl2.SDL_MaximizeWindow(p2d.window)
        for _ in range(5):
            p2d.get_events()
            game.draw()
            present()
        del resource
        print('PASS: HUD HP 100/37/0, dash 2/1/0, weapons/queue, bosses, save, restart cache, maximize')
    finally:
        p2d.update_canvas = present
        game.release_assets()
        p2d.close_canvas()


if __name__ == '__main__':
    main()
