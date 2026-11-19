"""실제 창에서 데모 구역 전투→이동→다음 전투→출구와 재시작 확인."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sdl2
from pico2d import pico2d as p2d
from main import MapGame
from tools.check_monster_maps import capture


def step(game, seconds):
    for _ in range(round(seconds * 60)):
        game.update(1 / 60)
        game.inputs.pressed.clear()


def defeat(game):
    for enemy in game.enemies:
        enemy.hp = 0
        enemy.on_combat_hit()
    step(game, 2)


def main():
    p2d.open_canvas(1280, 720, sync=True)
    game = MapGame()
    present = p2d.update_canvas
    try:
        p2d.update_canvas = lambda: None
        for index in (0, 1, 4, 5):
            game.enter_room(index)
            game.player.x = 1100
            game.camera.follow(game.player)
            game.draw()
            capture(f'johwarok-stage-{index}-battle1.png')
            present()
            p2d.get_events()
            defeat(game)
            assert game.encounters.completed == 1 and not game.room_clear
            game.player.x = 1500
            game.camera.follow(game.player)
            game.draw()
            capture(f'johwarok-stage-{index}-traversal.png')
            present()
            game.player.x = 1750
            game.update(.02)
            assert game.encounters.active_index == 1
            game.draw()
            capture(f'johwarok-stage-{index}-battle2.png')
            present()
            defeat(game)
            assert game.room_clear and game.encounters.gate is None
            game.player.x = game.stage.width - 115
            game.inputs.pressed = {sdl2.SDLK_UP}
            game.update(.02)
            assert game.room_index == index + 1
        game.enter_room(3)
        game.player.x = 640
        game.inputs.pressed = {sdl2.SDLK_UP}
        game.update(.02)
        game.enter_room(4)
        defeat(game)
        game.inputs.pressed = {sdl2.SDLK_r}
        game.update(.02)
        assert game.room_index == 3
        game.player.x = game.stage.width - 115
        game.inputs.pressed = {sdl2.SDLK_UP}
        game.update(.02)
        assert game.room_index == 4 and game.encounters.completed == 0
        game.draw()
        present()
        print('PASS: four normal maps, barriers, traversal, second groups, exits, checkpoint restart')
    finally:
        p2d.update_canvas = present
        game.release_assets()
        p2d.close_canvas()


if __name__ == '__main__':
    main()
