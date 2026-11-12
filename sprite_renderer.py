"""사용자 제공 데모 시트 렌더링. SDL 창이 열린 뒤 한 번 로드한다."""
from sprite_animation import ASSET_ROOT, CELL, HERO_SCALE, source_rect, draw_center


class DemoSprites:
    def __init__(self):
        from pico2d import pico2d as p2d
        self.hero = p2d.load_image(str(ASSET_ROOT / "hero.png"))
        self.background = p2d.load_image(str(ASSET_ROOT / "village.png"))
        self.dummy = p2d.load_image(str(ASSET_ROOT / "dummy.png"))
        self.font = p2d.load_font(str(ASSET_ROOT / "font.ttf"), 18)
        if (self.hero.w, self.hero.h) != (800, 800):
            raise ValueError("데모 hero.png는 800×800 시트여야 합니다.")

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
        self.font.draw(24, 710, "JOHWAROK / DEMO SPRITES", pale)
        self.font.draw(24, 615, f"HP {game.player.hp}/{game.player.max_hp}", pale)
        self.font.draw(24, 590, f"Weapon: {game.player.weapon.upper()}  Dash: {game.player.dash_charges}/2", pale)
        p2d.draw_rectangle(14, 10, 1265, 78, 16, 30, 43, filled=True)
        self.font.draw(28, 54, "Arrows: move   C: double jump   Down+C: drop   X: attack   Z: dash   Space: switch", pale)
        self.font.draw(28, 27, "Up: checkpoint / boss gate   R: restart   F2: collision box   Esc: quit", pale)
        if game.victory:
            self.font.draw(485, 375, "VICTORY - Old Dokkaebi defeated", (130, 250, 190))
            self.font.draw(515, 335, "R: retry   Esc: quit", pale)
        elif game.player.hp <= 0:
            self.font.draw(480, 405, "YOU DIED - R to restart", (255, 180, 180))
        elif game.checkpoint.can_activate(game.player):
            self.font.draw(420, 565, "Checkpoint active" if game.checkpoint.active else "UP: activate checkpoint", pale)
        elif game.at_boss_gate and not game.boss_active:
            self.font.draw(420, 565, "UP: challenge Old Dokkaebi", pale)
        if game.boss_active and not game.victory:
            self.font.draw(350, 625, f"Old Dokkaebi: {game.boss.pattern} / {game.boss.state}", pale)

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
