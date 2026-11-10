"""이동·점프·대시 상태. 향후 공격도 독립 상태로 추가한다."""

from settings import (GRAVITY, JUMP_SPEED, MAX_FALL_SPEED, MOVE_SPEED,
                      PHYSICS_STEP, PLAYER_HEIGHT, PLAYER_WIDTH,
                      DASH_SPEED, DASH_DURATION, DASH_INVULNERABLE,
                      DASH_GAP, DASH_RECHARGE, DASH_MAX_CHARGES)


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
        self.drop_platforms = set()
        self.dash_remaining = 0.0
        self.dash_invulnerability = 0.0
        self.dash_lockout = 0.0
        self.dash_direction = 1
        self.dash_charges = DASH_MAX_CHARGES
        self.recharge_remaining = 0.0
        self.hazard_exposed = False
        self.hazard_hits = 0

    @property
    def dash_invulnerable(self):
        return self.dash_invulnerability > 1e-9

    def end_dash_invulnerability(self):
        """점프 및 향후 공격/전환 시작 시 호출. 대시 이동은 유지한다."""
        self.dash_invulnerability = 0.0

    def start_dash(self):
        if self.dash_charges == 0 or self.dash_lockout > 1e-9:
            return False
        if self.dash_charges == DASH_MAX_CHARGES:
            self.recharge_remaining = DASH_RECHARGE
        self.dash_charges -= 1
        self.dash_direction = self.facing
        self.dash_remaining = DASH_DURATION
        self.dash_invulnerability = 0.0
        self.dash_lockout = DASH_DURATION + DASH_GAP
        return True

    def advance_dash_timers(self, step):
        self.dash_remaining = max(0.0, self.dash_remaining - step)
        self.dash_invulnerability = max(0.0, self.dash_invulnerability - step)
        self.dash_lockout = max(0.0, self.dash_lockout - step)
        if self.dash_charges < DASH_MAX_CHARGES:
            self.recharge_remaining -= step
            if self.recharge_remaining <= 1e-9:
                self.dash_charges += 1
                self.recharge_remaining = (DASH_RECHARGE + self.recharge_remaining
                    if self.dash_charges < DASH_MAX_CHARGES else 0.0)

    def update(self, dt, direction, jump_pressed, world, down_held=False,
               dash_pressed=False):
        if dt <= 0:
            return
        # 발판에서 걸어 나간 경우에도 공중 추가 점프는 한 번만 허용한다.
        self.drop_platforms = {s for s in self.drop_platforms if self.y >= s.top}
        supports = [s for s in world.solids
            if s not in self.drop_platforms and abs(self.y - s.top) < 1e-7
            and self.x < s.right and self.x + self.width > s.left
        ]
        self.grounded = bool(supports) and self.vy <= 0
        if self.grounded:
            self.jumps_used = 0
        else:
            self.jumps_used = max(1, self.jumps_used)
        if direction:
            self.facing = 1 if direction > 0 else -1
        if dash_pressed:
            self.start_dash()
        dropping = (jump_pressed and down_held and self.grounded
                    and all(s.one_way for s in supports))
        if dropping:
            self.end_dash_invulnerability()
            self.drop_platforms.update(supports)
            self.vy = -80.0  # 하강 시작용 임시 속도(px/s).
            self.jumps_used = 1
            self.grounded = False
        elif jump_pressed and self.jumps_used < 2:
            self.end_dash_invulnerability()
            self.vy = JUMP_SPEED
            self.jumps_used += 1
            self.grounded = False

        remaining = dt
        while remaining > 1e-9:
            step = min(remaining, PHYSICS_STEP)
            # 구간 경계에서 나누어 FPS에 따른 이동 거리·무적 시간 차이를 막는다.
            for timer in (self.dash_remaining, self.dash_invulnerability):
                if timer > 1e-9:
                    step = min(step, timer)
            remaining -= step
            speed = (self.dash_direction * DASH_SPEED if self.dash_remaining > 1e-9
                     else direction * MOVE_SPEED)
            world.move_x(self, speed * step)
            old_vy = self.vy
            self.vy = max(-MAX_FALL_SPEED, self.vy - GRAVITY * step)
            landed, hit = world.move_y(self, (old_vy + self.vy) * 0.5 * step,
                                      self.drop_platforms)
            self.grounded = landed
            if hit:
                self.vy = 0.0
            if landed:
                self.jumps_used = 0
            else:
                self.jumps_used = max(1, self.jumps_used)
            exposed = not self.dash_invulnerable and any(
                self.x < h.right and self.x + self.width > h.left
                and self.y < h.top and self.y + self.height > h.bottom
                for h in world.hazards)
            if exposed and not self.hazard_exposed:
                self.hazard_hits += 1
            self.hazard_exposed = exposed
            self.advance_dash_timers(step)
