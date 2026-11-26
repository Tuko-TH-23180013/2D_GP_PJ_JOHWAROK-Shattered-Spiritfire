"""실제 SDL 상자 정보/선택/획득과 일반·중간·메인 재화 분출 검사."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import sdl2
from pico2d import pico2d as p2d
from main import MapGame
from tools.check_monster_maps import capture
from tools.check_growth import click


def step(game, seconds):
    game.inputs.collect([])
    for _ in range(round(seconds*60)):
        game.update(1/60)


def main():
    p2d.open_canvas(1280,720,sync=True)
    game = MapGame()
    present = p2d.update_canvas
    try:
        p2d.update_canvas = lambda: None
        sdl2.SDL_RenderSetLogicalSize(p2d.renderer,1280,720)
        for enemy in game.enemies:
            enemy.hp = 0
            enemy.on_combat_hit()
        game.update(.15)
        assert len(game.rewards.currency_drops) == 4
        game.draw()
        capture('johwarok-currency-normal-burst.png')
        present()
        step(game,2)
        assert len(game.gear.chests) == 2
        for chest in game.gear.chests:
            game.player.x = chest.x
            game.camera.follow(game.player)
            game.draw()
            capture(f'johwarok-chest-{chest.kind}-world.png')
            present()
            game.inputs.pressed = {sdl2.SDLK_f}
            game.update(.016)
            assert game.gear.chest_open is chest
            point = (600,460) if chest.kind == 'item' else (800,460)
            event = sdl2.SDL_Event()
            event.type = sdl2.SDL_MOUSEMOTION
            event.motion.x,event.motion.y = point[0],719-point[1]
            game.inputs.collect([event])
            game.update(.016)
            game.draw()
            capture(f'johwarok-chest-{chest.kind}-hover.png')
            present()
            click(game,*point)
            click(game,640,200)
            assert chest.claimed
        assert game.abilities.equipped == 'blink' and any(game.gear.equipment.slots)
        for room,gold,jade in ((2,60,12),(6,210,42)):
            game.enter_room(room)
            game.player.x = game.boss.x-180
            game.camera.follow(game.player)
            game.boss.hp = 0
            game.boss.on_combat_hit()
            game.update(.15)
            assert game.rewards.currency_drops
            game.draw()
            capture(f'johwarok-currency-boss-{room}-burst.png')
            present()
            step(game,2)
            assert (game.rewards.gold,game.rewards.jade) == (gold,jade)
        game.restart()
        assert (game.rewards.gold,game.rewards.jade) == (0,42)
        game.draw()
        capture('johwarok-currency-new-run.png')
        present()
        print('PASS: chest hover/selection/claim, three-tier bursts, dual wallets, jade retention')
    finally:
        p2d.update_canvas = present
        game.release_assets()
        p2d.close_canvas()


if __name__ == '__main__':
    main()
