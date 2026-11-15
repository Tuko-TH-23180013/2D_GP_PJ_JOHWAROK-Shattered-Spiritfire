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
        x = monster.x + monster.width / 2 - camera.x + (cw / 2 - pivot_x) * scale
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
        try:
            image.clip_composite_draw(frame * cw, 0, cw, ch, angle,
                                      'h' if facing < 0 else '', x, y, cw * scale, ch * scale)
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
        p2d.draw_rectangle(b.left - camera.x, b.bottom, b.right - camera.x, b.top, *color)
        sx, sy = cue.start
        ex, ey = cue.end
        dx, dy = ex - sx, ey - sy
        length = max(1, (dx * dx + dy * dy) ** .5)
        ux, uy = dx / length, dy / length
        for i in range(1, max(2, int(length / 14))):
            t = i / max(2, int(length / 14))
            x, y = sx + dx * t - camera.x, sy + dy * t
            p2d.draw_rectangle(x - 2, y - 2, x + 2, y + 2, *color, filled=True)
        for side in (-1, 1):
            for i in range(8):
                x = ex - ux * i * 2 + side * uy * i - camera.x
                y = ey - uy * i * 2 - side * ux * i
                p2d.draw_rectangle(x - 1, y - 1, x + 1, y + 1, *color, filled=True)
        x = actor.x + actor.width / 2 - camera.x
        y = actor.y + actor.height + 40
        self.font.draw(x - 4, y + 12, '!', color)
        p2d.draw_rectangle(x - 30, y - 8, x + 30, y - 3, 75, 65, 35, filled=True)
        p2d.draw_rectangle(x - 30, y - 8, x - 30 + 60 * cue.progress, y - 3, *color, filled=True)

    def draw_background(self, camera):
        from pico2d import pico2d as p2d
        # 원본 배경의 데모 제목/조작 안내를 제외한 풍경 띠만 사용한다.
        p2d.draw_rectangle(0, 0, 1279, 719, 13, 22, 39, filled=True)
        offset = (camera.x * 0.15) % 1280
        for left in (-offset, 1280 - offset):
            self.background.clip_draw(0, 148, 960, 212, left + 640,
                                      100 + 212 * (1280 / 960) / 2,
                                      1280, 212 * (1280 / 960))
        self.background.clip_draw(700, 350, 200, 180, 1100, 550, 200, 180)

    def draw_dummy(self, dummy, camera):
        import sdl2
        if dummy.hp <= 0:
            return
        tint = (255, 140, 140) if dummy.hit_flash > 0 else (255, 255, 255)
        sdl2.SDL_SetTextureColorMod(self.dummy.texture, *tint)
        height = 65 if dummy.stagger_remaining > 0 else 90
        self.dummy.draw(dummy.x + dummy.width / 2 - camera.x, dummy.y + height / 2,
                        90 * self.dummy.w / self.dummy.h, height)
        sdl2.SDL_SetTextureColorMod(self.dummy.texture, 255, 255, 255)

    def draw_labels(self, game):
        from pico2d import pico2d as p2d
        pale = (210, 230, 235)
        self.hud.draw(game)
        if hasattr(game, 'room_index'):
            self.draw_route_labels(game)
            return
        if game.victory:
            self.font.draw(485, 375, "VICTORY - Old Dokkaebi defeated", (130, 250, 190))
            self.font.draw(515, 335, "R: retry   Esc: quit", pale)
        elif game.player.hp <= 0:
            self.font.draw(480, 405, "YOU DIED - R to restart", (255, 180, 180))
        elif game.checkpoint.can_activate(game.player):
            self.font.draw(420, 565, "Checkpoint active" if game.checkpoint.active else "UP: activate checkpoint", pale)
        elif game.at_boss_gate and not game.boss_active:
            self.font.draw(420, 565, "UP: challenge Old Dokkaebi", pale)
    def draw_route_labels(self, game):
        from pico2d import pico2d as p2d
        pale = (210, 230, 235)
        self.font.draw(24, 710, f'MAP {game.room_index + 1}/7 - {game.stage.name}', pale)
        labels = ('N1', 'N2', 'MID', 'SAVE', 'N3', 'N4', 'BOSS')
        for i, label in enumerate(labels):
            x = 365 + i * 116
            if i < 6:
                p2d.draw_rectangle(x + 74, 571, x + 116, 573, 95, 125, 145, filled=True)
            color = ((75, 165, 185) if i == game.room_index else
                     (45, 105, 65) if i in game.cleared_rooms else (45, 50, 65))
            p2d.draw_rectangle(x, 554, x + 74, 590, *color, filled=True)
            self.font.draw(x + 10, 572, label, pale)
        if game.victory:
            self.font.draw(465, 375, 'VICTORY - Guardian defeated!', (130, 250, 190))
            self.font.draw(480, 335, 'R: restart from save point', pale)
        elif game.player.hp <= 0:
            self.font.draw(480, 405, 'YOU DIED - R to restart', (255, 180, 180))
        elif game.stage.category == 'save':
            self.font.draw(380, 520, 'SAVE ACTIVE (this session)' if game.checkpoint.active
                           else 'UP at blue shrine: set respawn point', (120, 245, 210))
        elif not game.room_clear:
            remaining = sum(e.hp > 0 for e in game.enemies) + int(game.boss is not None and game.boss.hp > 0)
            self.font.draw(425, 520, f'Defeat all enemies to open exit: {remaining}', pale)
        if game.room_clear and not game.victory and game.player.hp > 0:
            self.font.draw(440, 488, 'Map clear - UP at the right gate', (140, 250, 190))
        gate = game.stage.boss_entrance
        self.font.draw(gate.left - game.camera.x - 15, gate.top + 25,
                       'UP: NEXT' if game.room_clear else 'LOCKED', pale)

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
                                          *draw_center(player, camera.x),
                                          CELL * HERO_SCALE, CELL * HERO_SCALE)
        finally:
            self.hero.opacify(1.0)
            sdl2.SDL_SetTextureColorMod(self.hero.texture, 255, 255, 255)
