"""사용자 제공 데모 시트 렌더링. SDL 창이 열린 뒤 한 번 로드한다."""
from sprite_animation import ASSET_ROOT, CELL, HERO_SCALE, source_rect, draw_center


class DemoSprites:
    def __init__(self):
        from pico2d import pico2d as p2d
        self.hero = p2d.load_image(str(ASSET_ROOT / "hero.png"))
        self.background = p2d.load_image(str(ASSET_ROOT / "village.png"))
        self.dummy = p2d.load_image(str(ASSET_ROOT / "dummy.png"))
        self.font = p2d.load_font(str(ASSET_ROOT / "font.ttf"), 18)
        self.monster_images = {}
        from Ui.HUD.renderer import HUD
        self.hud = HUD()
        if (self.hero.w, self.hero.h) != (800, 800):
            raise ValueError("데모 hero.png는 800×800 시트여야 합니다.")

    def draw_monster(self, monster, camera):
        from pico2d import pico2d as p2d
        from monster_sprites import CATALOG, pose
        import sdl2
        if monster.death_done:
            return
        sheet_id, frame = pose(monster)
        sheet = CATALOG[sheet_id]
        if sheet_id not in self.monster_images:
            self.monster_images[sheet_id] = p2d.load_image(str(sheet['file']))
        image = self.monster_images[sheet_id]
        cw, ch = sheet['frame_size']
        px, py = sheet['pico2d_pivot']
        # 원본 아트의 투명 여백 대신 실제 몸 높이로 배율을 통일한다.
        scale = monster.height / sheet['reference_body_height_px']
        facing = monster.attack.facing if monster.attack else monster.facing
        pivot_x = cw - px if facing < 0 else px
        anchor_y = monster.y + (monster.height / 2 if getattr(monster, 'flying', False) else 0)
        x = monster.x + monster.width / 2 + (cw / 2 - pivot_x) * scale
        y = anchor_y + (ch / 2 - py) * scale
        hurt = getattr(monster, 'hitstun_remaining', 0)
        angle = 0
        if hurt > 0:
            from math import sin
            from monsters import NORMAL_HITSTUN
            age = NORMAL_HITSTUN - hurt
            # 데모 회수 포즈에 짧은 반동/떨림을 더한다. 실제 충돌 위치는 유지한다.
            recoil = max(0, 1 - age / .20)
            x -= facing * 8 * recoil
            angle = facing * (.10 + .04 * sin(age * 55)) * min(1, hurt / .1)
        tint = (255, 140, 140) if monster.hit_flash > 0 else (255, 255, 255)
        sdl2.SDL_SetTextureColorMod(image.texture, *tint)
        x, y = camera.screen_point(x, y)
        try:
            image.clip_composite_draw(frame * cw, 0, cw, ch, angle,
                                      'h' if facing < 0 else '', x, y, cw * scale * camera.zoom, ch * scale * camera.zoom)
        finally:
            sdl2.SDL_SetTextureColorMod(image.texture, 255, 255, 255)

    def draw_attack_telegraph(self, actor, camera):
        from pico2d import pico2d as p2d
        from attack_telegraph import attack_telegraph
        cue = attack_telegraph(actor)
        if cue is None:
            return
        color = (255, 220, 60) if int(cue.progress * 8) % 2 == 0 else (255, 145, 40)
        b = cue.bounds
        # 경로 예상치이며 벽 정지/회피에 따라 실제 도달 위치는 달라진다.
        p2d.draw_rectangle(*camera.screen_rect(b.left, b.bottom, b.right, b.top), *color)
        sx, sy = cue.start
        ex, ey = cue.end
        dx, dy = ex - sx, ey - sy
        length = max(1, (dx * dx + dy * dy) ** .5)
        ux, uy = dx / length, dy / length
        for i in range(1, max(2, int(length / 14))):
            t = i / max(2, int(length / 14))
            x, y = sx + dx * t, sy + dy * t
            p2d.draw_rectangle(*camera.screen_rect(x - 2, y - 2, x + 2, y + 2), *color, filled=True)
        for side in (-1, 1):
            for i in range(8):
                x = ex - ux * i * 2 + side * uy * i
                y = ey - uy * i * 2 - side * ux * i
                p2d.draw_rectangle(*camera.screen_rect(x - 1, y - 1, x + 1, y + 1), *color, filled=True)
        x, y = camera.screen_point(actor.x + actor.width / 2, actor.y + actor.height + 40)
        self.font.draw(x - 4, y + 12, '!', color)
        p2d.draw_rectangle(x - 30, y - 8, x + 30, y - 3, 75, 65, 35, filled=True)
        p2d.draw_rectangle(x - 30, y - 8, x - 30 + 60 * cue.progress, y - 3, *color, filled=True)

    def draw_background(self, camera):
        from pico2d import pico2d as p2d
        # 원본 배경의 데모 제목/조작 안내를 제외한 풍경 띠만 사용한다.
        p2d.draw_rectangle(0, 0, 1279, 719, 13, 22, 39, filled=True)
        width = 1280 * camera.zoom
        height = 212 * (1280 / 960) * camera.zoom
        offset = (camera.x * camera.zoom * 0.15) % width
        floor_y = camera.ground_screen_y - camera.y * camera.zoom * .15
        for left in (-offset, width - offset):
            self.background.clip_draw(0, 148, 960, 212, left + width / 2,
                                      floor_y + height / 2, width, height)
        self.background.clip_draw(700, 350, 200, 180, 1100, 550, 200, 180)

    def draw_dummy(self, dummy, camera):
        import sdl2
        if dummy.hp <= 0:
            return
        tint = (255, 140, 140) if dummy.hit_flash > 0 else (255, 255, 255)
        sdl2.SDL_SetTextureColorMod(self.dummy.texture, *tint)
        height = 65 if dummy.stagger_remaining > 0 else 90
        self.dummy.draw(*camera.screen_point(dummy.x + dummy.width / 2, dummy.y + height / 2),
                        90 * self.dummy.w / self.dummy.h * camera.zoom, height * camera.zoom)
        sdl2.SDL_SetTextureColorMod(self.dummy.texture, 255, 255, 255)

    def draw_labels(self, game):
        self.hud.draw(game)

    def draw_hero(self, player, animation, camera):
        import sdl2
        facing = (player.attack.facing if player.attack is not None else
                  player.dash_direction if player.dash_remaining > 1e-9 else player.facing)
        tint = (255, 120, 120) if player.hit_flash > 0 else (255, 255, 255)
        sdl2.SDL_SetTextureColorMod(self.hero.texture, *tint)
        self.hero.opacify(0.65 if player.invulnerable else 1.0)
        try:
            self.hero.clip_composite_draw(*source_rect(animation.frame), 0,
                                          'h' if facing < 0 else '',
                                          *camera.screen_point(*draw_center(player, 0)),
                                          CELL * HERO_SCALE * camera.zoom, CELL * HERO_SCALE * camera.zoom)
        finally:
            self.hero.opacify(1.0)
            sdl2.SDL_SetTextureColorMod(self.hero.texture, 255, 255, 255)
