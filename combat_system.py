"""공격 충돌·무적·HP 피해·스태거 처리. 행동 AI는 포함하지 않는다."""


def overlaps(a, b):
    return (a.left < b.right and a.right > b.left
            and a.bottom < b.top and a.top > b.bottom)


class CombatSystem:
    def __init__(self):
        self.damaged_this_frame = set()

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
                if not overlaps(attack.bounds, target.bounds):
                    continue
                attack.hit_targets.add(target)
                self.damaged_this_frame.add(target)
                target.hp = max(0, target.hp - attack.data.damage)
                target.hit_flash = 0.12
                if hasattr(target, "hurt_invulnerability"):
                    target.hurt_invulnerability = target.hurt_invulnerability_duration
                if target.stagger_limit is not None and target.stagger_remaining <= 0:
                    target.stagger = min(target.stagger_limit,
                                         target.stagger + attack.data.stagger)
                    if target.stagger >= target.stagger_limit:
                        target.stagger_remaining = 0.6
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
