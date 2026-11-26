"""공격별 임시 수치와 공격 한 번의 수명·방향·명중 기록."""

from dataclasses import dataclass
from world import Rect


@dataclass(frozen=True)
class AttackData:
    name: str
    startup: float
    active: float
    recovery: float
    damage: int
    stagger: int
    reach: float
    height: float


# 3단계 연습용 임시 수치. 기획 확정 수치가 아니다.
BASIC_COMBO = (
    AttackData("Ground 1", 0.10, 0.10, 0.18, 10, 15, 75, 55),
    AttackData("Ground 2", 0.12, 0.10, 0.20, 12, 20, 85, 60),
    AttackData("Ground 3", 0.16, 0.12, 0.28, 18, 30, 105, 70),
)
AIR_ATTACK = AttackData("Air", 0.10, 0.12, 0.20, 12, 18, 80, 70)


class Attack:
    def __init__(self, owner, data, airborne=False, combo_index=0):
        self.owner = owner
        self.data = data
        self.airborne = airborne
        self.combo_index = combo_index
        self.facing = owner.facing
        self.elapsed = 0.0
        self.hit_targets = set()

    @property
    def phase(self):
        if self.elapsed < self.data.startup - 1e-9:
            return "STARTUP"
        if self.elapsed < self.data.startup + self.data.active - 1e-9:
            return "ACTIVE"
        if self.elapsed < self.data.startup + self.data.active + self.data.recovery - 1e-9:
            return "RECOVERY"
        return "DONE"

    @property
    def bounds(self):
        scale = getattr(self.owner, 'body_scale', 1)
        half = self.owner.width * scale / 2
        center = self.owner.x + self.owner.width / 2
        edge = center + self.facing * half
        reach, height = self.data.reach * scale, self.data.height * scale
        left = edge if self.facing > 0 else edge - reach
        bottom = self.owner.y + (self.owner.height * scale - height) / 2
        return Rect(left, bottom, left + reach, bottom + height)

    def advance(self, dt):
        self.elapsed += dt
