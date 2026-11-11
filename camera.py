"""그리기에만 적용하는 수평 카메라. 월드 충돌 좌표는 변경하지 않는다."""
from settings import WINDOW_WIDTH


class Camera:
    def __init__(self, world_width, view_width=WINDOW_WIDTH):
        self.world_width = world_width
        self.view_width = view_width
        self.x = 0.0

    def follow(self, player):
        self.x = max(0.0, min(player.x + player.width / 2 - self.view_width / 2,
                             max(0.0, self.world_width - self.view_width)))

    def screen_rect(self, left, bottom, right, top):
        return left - self.x, bottom, right - self.x, top
