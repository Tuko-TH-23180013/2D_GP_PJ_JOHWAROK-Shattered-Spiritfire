"""실제 SDL 데모 장비창, 마우스 이벤트, 능력 HUD와 확대 판정 검사."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sdl2
from pico2d import pico2d as p2d
from main import MapGame
from tools.check_monster_maps import capture


def click(game, x, y):
    event = sdl2.SDL_Event()
    event.type = sdl2.SDL_MOUSEBUTTONDOWN
    event.button.button = sdl2.SDL_BUTTON_LEFT
    event.button.x, event.button.y = x, 719-y
    game.inputs.collect([event])
    game.update(.016)


def main():
    p2d.open_canvas(1280, 720, sync=True)
    game = MapGame()
    present = p2d.update_canvas
    try:
        sdl2.SDL_RenderSetLogicalSize(p2d.renderer, 1280, 720)
        p2d.update_canvas = lambda: None
        for slot, item in enumerate(('fang', 'fang', 'mirror', 'guard_knot')):
            game.gear.equipment.equip(slot, item)
        game.player.refresh_stats()
        game.gear.special_choices = True
        game.gear.open = True
        game.draw()
        capture('johwarok-growth-equipment.png')
        present()
        click(game, 750, 200)
        assert game.abilities.equipped == 'enlarge'
        before = game.elapsed
        game.update(30)
        assert game.elapsed == before
        click(game, 1040, 610)
        assert not game.gear.open
        game.inputs.collect([])
        game.player.x = 350
        game.inputs.pressed = {sdl2.SDLK_LSHIFT}
        game.update(.016)
        assert game.player.body_scale > 1
        game.show_hitboxes = True
        game.inputs.pressed.clear()
        game.player.start_attack()
        game.draw()
        capture('johwarok-growth-giant.png')
        present()
        game.gear.open = True
        before = (game.player.attack.elapsed, game.abilities.giant_remaining,
                  dict(game.abilities.cooldowns), game.player.x)
        game.inputs.collect([])
        game.update(30)
        assert before == (game.player.attack.elapsed, game.abilities.giant_remaining,
                          game.abilities.cooldowns, game.player.x)
        drop = game.gear.add_drop('stone', game.player)
        game.gear.pending = drop
        game.draw()
        capture('johwarok-growth-replace.png')
        present()
        click(game, 300, 490)
        assert drop.consumed and game.gear.equipment.slots[0] == 'stone'
        assert game.gear.drops[-1].item_id == 'fang'
        game.enter_room(3, hp=70)
        game.gear.open = True
        click(game, 940, 390)
        assert game.player.weapon == 'giant'
        game.draw()
        capture('johwarok-growth-safe-form.png')
        present()
        game.gear.open = False
        game.abilities.owned.add('blink')  # 교체 HUD 검사용 fixture
        game.abilities.equip('blink')
        events = []
        for key in (sdl2.SDLK_RIGHT, sdl2.SDLK_UP, sdl2.SDLK_LSHIFT):
            event = sdl2.SDL_Event()
            event.type = sdl2.SDL_KEYDOWN
            event.key.keysym.sym = key
            events.append(event)
        before_x, before_y = game.player.x, game.player.y
        game.inputs.collect(events)
        game.update(.016)
        assert game.player.x > before_x + 150 and game.player.y > before_y + 150
        assert game.abilities.cooldowns['blink'] > 0
        game.draw()
        capture('johwarok-growth-cooldowns.png')
        present()
        game.restart()
        assert game.player.max_hp == game.player.hp == 100
        assert not game.abilities.owned and not any(game.gear.equipment.slots)
        game.draw()
        present()
        print('PASS: SDL mouse gear/replace/forms, pause, Shift giant, independent HUD, reset')
    finally:
        p2d.update_canvas = present
        game.release_assets()
        p2d.close_canvas()


if __name__ == '__main__':
    main()
