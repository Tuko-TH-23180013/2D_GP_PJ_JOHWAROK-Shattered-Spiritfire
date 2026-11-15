"""실제 SDL 창에서 7개 맵·모든 데모 시트·재시작 캐시를 검사한다."""
from pathlib import Path
import ctypes
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sdl2
from sdl2.sdlimage import IMG_SavePNG
from pico2d import pico2d as p2d
from main import MapGame
from monster_sprites import CATALOG
from attack import Attack
from demo_bosses import SWING, SLASH, RUSH


def capture(name):
    surface = sdl2.SDL_CreateRGBSurfaceWithFormat(0, 1280, 720, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    assert surface
    try:
        assert sdl2.SDL_RenderReadPixels(p2d.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888,
                                       surface.contents.pixels, surface.contents.pitch) == 0
        path = Path(tempfile.gettempdir()) / name
        assert IMG_SavePNG(surface, str(path).encode('utf-8')) == 0
        print('CAPTURE:', path)
    finally:
        sdl2.SDL_FreeSurface(surface)


def main():
    p2d.open_canvas(1280, 720, sync=True)
    game = MapGame()
    present = p2d.update_canvas
    try:
        p2d.update_canvas = lambda: None
        for i in range(7):
            game.enter_room(i)
            game.player.x = 450
            game.update(.02)
            for actor in game.enemies + ([game.boss] if game.boss else []):
                data = actor.spec.attack if hasattr(actor, 'spec') else SLASH if i == 2 else RUSH
                actor.attack = Attack(actor, data)
                actor.attack.elapsed = data.startup * .65
                actor.state = 'STARTUP'
                if i == 6:
                    actor.pattern, actor.sheet = 'RUSH', 'guardian'
                if getattr(actor, 'kind', '') == 'sotdae':
                    actor.dive_velocity = (-400, -150)
            game.draw()
            capture(f'johwarok-map-{i + 1}.png')
            present()
            p2d.get_events()
        game.enter_room(0)
        game.player.x = 450
        game.enemies[0].on_combat_hit()
        game.draw()
        capture('johwarok-normal-hitstun.png')
        present()
        # 모든 PNG가 SDL에서 실제 로드/클립/좌우 반전되는지 검사.
        for sheet_id, sheet in CATALOG.items():
            image = p2d.load_image(str(sheet['file']))
            cw, ch = sheet['frame_size']
            assert (image.w, image.h) == (cw * len(sheet['frames']), ch)
            for flip in ('', 'h'):
                for frame in sheet['frames']:
                    image.clip_composite_draw(frame['index'] * cw, 0, cw, ch, 0, flip,
                                              640, 300, cw * .4, ch * .4)
                present()
                p2d.get_events()
            del image
        game.enter_room(2)
        game.player.x = 850
        game.camera.follow(game.player)
        game.boss.stagger_remaining = 2
        game.boss.on_combat_hit()
        game.draw()
        capture('johwarok-mid-down.png')
        present()
        game.enter_room(6)
        game.player.x = 950
        game.camera.follow(game.player)
        game.boss.attack = Attack(game.boss, SWING)
        game.boss.attack.elapsed = SWING.startup
        game.boss.state = 'ACTIVE'
        game.draw()
        capture('johwarok-main-attack.png')
        present()
        game.enter_room(3)
        game.player.x = 640
        game.inputs.pressed = {sdl2.SDLK_UP}
        game.update(.02)
        assert game.saved_room == 3
        resources = game.visuals
        game.enter_room(4)
        game.player.hp = 0
        game.inputs.pressed = {sdl2.SDLK_r}
        game.update(.02)
        game.draw()
        present()
        assert game.visuals is resources and game.room_index == 3
        del resources
        print(f'PASS: 7 maps, {len(CATALOG)} sheets in both directions, boss poses, save/restart/cache')
    finally:
        p2d.update_canvas = present
        game.release_assets()
        p2d.close_canvas()


if __name__ == '__main__':
    main()
