"""두 방망이의 공격 데이터. 모든 수치는 4단계 임시 조정값이다."""

from dataclasses import dataclass
from attack import AttackData, BASIC_COMBO, AIR_ATTACK


@dataclass(frozen=True)
class WeaponData:
    name: str
    combo: tuple[AttackData, ...]
    air: AttackData


WEAPONS = {
    "basic": WeaponData("Basic", BASIC_COMBO, AIR_ATTACK),
    "giant": WeaponData("Giant", (
        AttackData("Giant 1", 0.22, 0.16, 0.30, 24, 35, 120, 85),
        AttackData("Giant 2", 0.28, 0.18, 0.38, 36, 50, 150, 100),
    ), AttackData("Giant Air", 0.20, 0.16, 0.30, 26, 35, 125, 95)),
}
