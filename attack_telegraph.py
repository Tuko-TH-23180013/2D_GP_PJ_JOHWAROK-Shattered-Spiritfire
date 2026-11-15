"""판정과 독립적인 임시 공격 예고. 이동 공격은 예정 경로를 표시한다."""
from dataclasses import dataclass
from world import Rect


@dataclass(frozen=True)
class Telegraph:
    bounds: Rect
    start: tuple
    end: tuple
    progress: float


def attack_telegraph(actor):
    attack = actor.attack
    if actor.hp <= 0 or attack is None or attack.phase != 'STARTUP':
        return None
    box = attack.bounds
    start = (actor.x + actor.width / 2, actor.y + actor.height / 2)
    dx = dy = 0
    kind = getattr(actor, 'kind', '')
    pattern = getattr(actor, 'pattern', '')
    if kind == 'ember':
        dx = attack.facing * 310 * 2.5
        box = Rect(start[0] - 12, start[1] - 9, start[0] + 12, start[1] + 9)
    elif kind == 'sotdae':
        vx, vy = actor.dive_velocity
        dx, dy = vx * attack.data.active, vy * attack.data.active
    elif kind == 'mask':
        dx = attack.facing * 260 * attack.data.active
    elif kind in ('onggi', 'jige') or pattern in ('RUSH', 'THRUST'):
        speed = {'onggi': 180, 'jige': 390}.get(kind, 600 if pattern == 'RUSH' else 210)
        dx = attack.facing * speed * attack.data.active
    bounds = Rect(min(box.left, box.left + dx), min(box.bottom, box.bottom + dy),
                  max(box.right, box.right + dx), max(box.top, box.top + dy))
    end = (start[0] + dx, start[1] + dy) if dx or dy else (
        box.right if attack.facing > 0 else box.left, (box.bottom + box.top) / 2)
    return Telegraph(bounds, start, end, min(1, attack.elapsed / max(.001, attack.data.startup)))
