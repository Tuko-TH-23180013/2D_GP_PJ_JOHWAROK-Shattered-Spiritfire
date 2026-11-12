"""사용자 제공 데모 시트 렌더링. SDL 창이 열린 뒤 한 번 로드한다."""
from sprite_animation import ASSET_ROOT, CELL, HERO_SCALE, source_rect, draw_center


class DemoSprites:
    def __init__(self):
        from pico2d import pico2d as p2d
        self.hero = p2d.load_image(str(ASSET_ROOT / "hero.png"))
        if (self.hero.w, self.hero.h) != (800, 800):
            raise ValueError("데모 hero.png는 800×800 시트여야 합니다.")

    def draw_hero(self, player, animation, camera):
        import sdl2
        facing = player.attack.facing if player.attack is not None else player.facing
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
