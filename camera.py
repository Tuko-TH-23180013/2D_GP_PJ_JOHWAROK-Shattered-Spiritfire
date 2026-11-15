"""배율·수평/수직 추적을 그리기에만 적용한다. 월드 충돌 좌표는 유지한다."""
from settings import WINDOW_WIDTH, WINDOW_HEIGHT


class Camera:
    def __init__(self, world_width, view_width=WINDOW_WIDTH, zoom=1.0,
                 ground_screen_y=100, vertical_follow=False):
        if zoom <= 0:
            raise ValueError('Camera zoom must be positive')
        self.world_width = world_width
        self.view_width = view_width
        self.zoom = zoom
        self.ground_screen_y = ground_screen_y
        self.vertical_follow = vertical_follow
        self.x = 0.0
        self.y = 0.0

    @property
    def visible_width(self):
        return self.view_width / self.zoom

    def follow(self, player):
        if self.world_width < self.visible_width:
            self.x = (self.world_width - self.visible_width) / 2
        else:
            self.x = max(0.0, min(player.x + player.width / 2 - self.visible_width / 2,
                                 self.world_width - self.visible_width))
        if self.vertical_follow:
            self.y = max(0.0, player.y + player.height - 100 - (WINDOW_HEIGHT - self.ground_screen_y - 100) / self.zoom)

    def screen_point(self, x, y):
        return ((x - self.x) * self.zoom,
                self.ground_screen_y + (y - 100 - self.y) * self.zoom)

    def screen_rect(self, left, bottom, right, top):
        return (*self.screen_point(left, bottom), *self.screen_point(right, top))
