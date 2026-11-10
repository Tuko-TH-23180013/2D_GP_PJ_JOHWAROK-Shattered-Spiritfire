"""플레이어 구조와 좌우 이동."""
from settings import MOVE_SPEED, PLAYER_WIDTH, PLAYER_HEIGHT
class Player:
    width = PLAYER_WIDTH
    height = PLAYER_HEIGHT
    def __init__(self, x=120.0, y=100.0):
        self.x, self.y = x, y
        self.vy = 0.0
        self.facing = 1
        self.grounded = True
        self.jumps_used = 0
    def update(self, dt, direction, jump_pressed, world):
        if direction:
            self.facing = 1 if direction > 0 else -1
        world.move_x(self, direction * MOVE_SPEED * dt)
