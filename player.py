"""이동과 점프 상태. 향후 대시·공격은 독립 상태로 추가한다."""

from settings import (GRAVITY, JUMP_SPEED, MAX_FALL_SPEED, MOVE_SPEED,
                      PHYSICS_STEP, PLAYER_HEIGHT, PLAYER_WIDTH)


class Player:
    width = PLAYER_WIDTH
    height = PLAYER_HEIGHT

    def __init__(self, x=120.0, y=100.0):
        self.x = x
        self.y = y
        self.vy = 0.0
        self.facing = 1
        self.grounded = False
        self.jumps_used = 0

    def update(self, dt, direction, jump_pressed, world):
        if dt <= 0:
            return
        # 발판에서 걸어 나간 경우에도 공중 추가 점프는 한 번만 허용한다.
        supported = any(
            abs(self.y - s.top) < 1e-7
            and self.x < s.right and self.x + self.width > s.left
            for s in world.solids
        )
        self.grounded = supported and self.vy <= 0
        if self.grounded:
            self.jumps_used = 0
        else:
            self.jumps_used = max(1, self.jumps_used)
        if direction:
            self.facing = 1 if direction > 0 else -1
        if jump_pressed and self.jumps_used < 2:
            self.vy = JUMP_SPEED
            self.jumps_used += 1
            self.grounded = False

        remaining = dt
        while remaining > 1e-9:
            step = min(remaining, PHYSICS_STEP)
            remaining -= step
            world.move_x(self, direction * MOVE_SPEED * step)
            old_vy = self.vy
            self.vy = max(-MAX_FALL_SPEED, self.vy - GRAVITY * step)
            landed, hit = world.move_y(self, (old_vy + self.vy) * 0.5 * step)
            self.grounded = landed
            if hit:
                self.vy = 0.0
            if landed:
                self.jumps_used = 0
            else:
                self.jumps_used = max(1, self.jumps_used)
