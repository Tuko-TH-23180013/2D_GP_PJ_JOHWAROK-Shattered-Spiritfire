"""이동·점프·대시·공격을 독립 상태로 관리한다."""

from attack import Attack
from weapon_data import WEAPONS
from world import Rect

from settings import (GRAVITY, JUMP_SPEED, MAX_FALL_SPEED, MOVE_SPEED,
                      PHYSICS_STEP, PLAYER_HEIGHT, PLAYER_WIDTH,
                      DASH_SPEED, DASH_DURATION, DASH_INVULNERABLE,
                      DASH_GAP, DASH_RECHARGE, DASH_MAX_CHARGES, SWITCH_DURATION,
                      SWITCH_INVULNERABLE)


class Player:
    width = PLAYER_WIDTH
    height = PLAYER_HEIGHT

    def __init__(self, x=120.0, y=100.0, weapon="basic"):
        if weapon not in WEAPONS:
            raise ValueError(f"알 수 없는 무기: {weapon}")
        self.weapon = weapon
        self.team = "player"
        self.max_hp = self.hp = 100
        self.hit_flash = 0.0
        self.hurt_invulnerability = 0.0
        self.hurt_invulnerability_duration = 0.5  # 임시 피격 후 무적.
        self.stagger = 0
        self.stagger_limit = None  # 생존 중 피격은 공격·콤보를 끊지 않는다.
        self.stagger_remaining = 0.0
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
        self.attack = None
        self.attack_queued = False
        self.switch_queued = False
        self.switch_remaining = 0.0
        self.switch_invulnerability = 0.0

    @property
    def bounds(self):
        return Rect(self.x, self.y, self.x + self.width, self.y + self.height)

    @property
    def invulnerable(self):
        return (self.dash_invulnerable or self.switch_invulnerability > 1e-9
                or self.hurt_invulnerability > 1e-9)

    def request_switch(self):
        if self.hp <= 0 or self.switch_remaining > 1e-9:
            return False
        if self.attack is not None:
            self.switch_queued = True
            return False
        self.perform_switch()
        return True

    def perform_switch(self):
        self.weapon = "giant" if self.weapon == "basic" else "basic"
        self.attack = None
        self.attack_queued = False
        self.switch_queued = False
        self.switch_remaining = SWITCH_DURATION
        self.switch_invulnerability = SWITCH_INVULNERABLE
        self.end_dash_invulnerability()

    def start_attack(self, combo_index=0):
        if self.hp <= 0:
            return
        airborne = not self.grounded
        weapon = WEAPONS[self.weapon]
        data = weapon.air if airborne else weapon.combo[combo_index]
        self.attack = Attack(self, data, airborne, 0 if airborne else combo_index)
        self.attack_queued = False
        self.end_dash_invulnerability()

    def request_attack(self):
        if self.hp <= 0 or self.switch_remaining > 1e-9:
            return
        if self.attack is None:
            self.start_attack()
        else:
            # 현재 공격 중 추가 X 입력은 다음 공격 한 번만 예약한다.
            self.attack_queued = True

    def advance_attack(self, dt):
        if self.attack is None:
            return
        self.attack.advance(dt)
        if self.attack.phase == "DONE":
            previous = self.attack
            queued = self.attack_queued
            self.attack = None
            self.attack_queued = False
            if self.switch_queued:
                self.perform_switch()
            elif queued:
                index = ((previous.combo_index + 1) % len(WEAPONS[self.weapon].combo)
                         if not previous.airborne and self.grounded else 0)
                self.start_attack(index)

    @property
    def dash_invulnerable(self):
        return self.dash_invulnerability > 1e-9

    def end_dash_invulnerability(self):
        """점프 및 향후 공격/전환 시작 시 호출. 대시 이동은 유지한다."""
        self.dash_invulnerability = 0.0

    def start_dash(self):
        if self.hp <= 0:
            return False
        if self.attack is not None and self.attack.phase in ("STARTUP", "ACTIVE"):
            return False
        if self.dash_charges == 0 or self.dash_lockout > 1e-9:
            return False
        self.attack = None
        self.attack_queued = False
        if self.dash_charges == DASH_MAX_CHARGES:
            self.recharge_remaining = DASH_RECHARGE
        self.dash_charges -= 1
        self.dash_direction = self.facing
        self.dash_remaining = DASH_DURATION
        self.dash_invulnerability = DASH_INVULNERABLE
        self.dash_lockout = DASH_DURATION + DASH_GAP
        if self.switch_queued:
            self.perform_switch()
        return True

    def on_combat_hit(self):
        if self.hp > 0:
            return
        self.attack = None
        self.attack_queued = self.switch_queued = False
        self.dash_remaining = self.dash_invulnerability = self.dash_lockout = 0.0
        self.switch_remaining = self.switch_invulnerability = 0.0
        self.hurt_invulnerability = 0.0
        self.vy = 0.0

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
               dash_pressed=False, attack_pressed=False, switch_pressed=False):
        if dt <= 0 or self.hp <= 0:
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
        if direction and self.attack is None:
            self.facing = 1 if direction > 0 else -1
        if dash_pressed:
            self.start_dash()
        if switch_pressed:
            self.request_switch()
        elif attack_pressed and not dash_pressed:
            self.request_attack()
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
            for timer in (self.dash_remaining, self.dash_invulnerability,
                          self.switch_invulnerability):
                if timer > 1e-9:
                    step = min(step, timer)
            remaining -= step
            speed = (self.dash_direction * DASH_SPEED if self.dash_remaining > 1e-9
                     else direction * MOVE_SPEED)
            world.move_x(self, speed * step)
            if self.dash_remaining > 1e-9:
                # ?? ??? ??/?? ??? ??? ?? ?? ??? ????.
                self.grounded = self.vy <= 0 and any(
                    s not in self.drop_platforms and abs(self.y - s.top) < 1e-7
                    and self.x < s.right and self.x + self.width > s.left
                    for s in world.solids)
            else:
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
            exposed = not self.invulnerable and any(
                self.x < h.right and self.x + self.width > h.left
                and self.y < h.top and self.y + self.height > h.bottom
                for h in world.hazards)
            if exposed and not self.hazard_exposed:
                self.hazard_hits += 1
            self.hazard_exposed = exposed
            self.advance_dash_timers(step)
            self.switch_remaining = max(0.0, self.switch_remaining - step)
            self.switch_invulnerability = max(0.0, self.switch_invulnerability - step)
            self.advance_attack(step)
