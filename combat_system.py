"""공격 충돌·무적·HP 피해·스태거 처리. 행동 AI는 포함하지 않는다."""


def overlaps(a, b):
    return (a.left < b.right and a.right > b.left
            and a.bottom < b.top and a.top > b.bottom)


class CombatSystem:
    def __init__(self, world=None):
        self.world = world
        self.damaged_this_frame = set()

    def blocked(self, attack, target):
        if self.world is None:
            return False
        # 확대된 판정이 벽/결계 반대편의 상대에게 닿아도 관통 피해는 금지.
        owner = attack.owner
        ax = getattr(attack, 'x', owner.x) + getattr(attack, 'width', owner.width) / 2
        bx = target.x + target.width / 2
        low, high = sorted((ax, bx))
        bounds = attack.bounds
        return any(not s.one_way and low <= s.left and s.right <= high
                   and bounds.bottom < s.top and bounds.top > s.bottom
                   for s in self.world.solids)

    def begin_frame(self):
        self.damaged_this_frame.clear()

    def resolve(self, attacks, targets):
        # 동시 공격 우선순위는 임시로 전달 순서. 대상당 프레임 1회 피해.
        for attack in attacks:
            if attack.phase != "ACTIVE" or getattr(attack.owner, "hp", 1) <= 0:
                continue
            for target in targets:
                if (target is attack.owner or target.hp <= 0 or target.invulnerable
                        or (getattr(target, "team", None) is not None
                            and target.team == getattr(attack.owner, "team", None))
                        or target in attack.hit_targets
                        or target in self.damaged_this_frame):
                    continue
                if (not overlaps(attack.bounds, getattr(target, 'hurt_bounds', target.bounds))
                        or self.blocked(attack, target)):
                    continue
                attack.hit_targets.add(target)
                self.damaged_this_frame.add(target)
                damage = (attack.data.damage * getattr(attack.owner, 'damage_multiplier', 1)
                          * (1 - getattr(target, 'damage_reduction', 0)))
                # 시험 정책: 최종 피해만 사사오입, 내부 HP는 정수로 유지.
                target.hp = max(0, target.hp - max(0, int(damage + .5)))
                target.hit_flash = 0.12
                if hasattr(target, "hurt_invulnerability"):
                    target.hurt_invulnerability = target.hurt_invulnerability_duration
                if (target.stagger_limit is not None and target.stagger_remaining <= 0
                        and getattr(target, "can_accumulate_stagger", True)):
                    target.stagger = min(target.stagger_limit,
                                         target.stagger + attack.data.stagger *
                                         getattr(attack.owner, 'stagger_multiplier', 1))
                    if target.stagger >= target.stagger_limit:
                        target.stagger_remaining = getattr(target, "stagger_duration", 0.6)
                if hasattr(target, "on_combat_hit"):
                    target.on_combat_hit()

    def update_target(self, target, dt):
        target.hit_flash = max(0.0, target.hit_flash - dt)
        if hasattr(target, "hurt_invulnerability"):
            target.hurt_invulnerability = max(0.0, target.hurt_invulnerability - dt)
        if target.stagger_remaining > 0:
            target.stagger_remaining = max(0.0, target.stagger_remaining - dt)
            if target.stagger_remaining <= 1e-9:
                target.stagger_remaining = 0.0
                target.stagger = 0
