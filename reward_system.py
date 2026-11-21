"""처치 보상. 강화용 혼불은 현재 실행 세션 동안 유지한다."""

from dataclasses import dataclass
import random

REWARD_CURRENCY = {'normal': 5, 'mid': 50, 'main': 150}  # 임시 밸런스
ORB_DROP_CHANCE = .25
ORB_HEAL = 20
MID_BOSS_HEAL = 40


def heal(player, amount):
    """회복은 무적/피격과 독립적이며 사망한 캐릭터를 부활시키지 않는다."""
    if player.hp <= 0:
        return 0
    before = player.hp
    player.hp = min(player.max_hp, player.hp + max(0, amount))
    return player.hp - before


@dataclass
class VitalityOrb:
    x: float
    y: float
    width: float = 20
    height: float = 20
    vy: float = 0

    def update(self, dt, world, player):
        self.vy = max(-600, self.vy - 900 * dt)
        _, hit = world.move_y(self, self.vy * dt)
        if hit:
            self.vy = 0
        touching = (self.x < player.x + player.width and self.x + self.width > player.x
                    and self.y < player.y + player.height and self.y + self.height > player.y)
        return touching and heal(player, ORB_HEAL) > 0


class RewardSystem:
    def __init__(self, rng=None):
        self.rng = rng if rng is not None else random.Random()
        self.balance = 0
        self.reset_room()

    def reset_room(self):
        # 객체 자체를 보관하여 제거된 적의 id 재사용도 방지한다.
        self.credited = set()
        self.orbs = []

    def collect_defeats(self, actors, boss=None, category='normal', player=None):
        for actor in actors:
            if actor.hp > 0 or actor in self.credited:
                continue
            self.credited.add(actor)
            tier = category if actor is boss else 'normal'
            self.balance += REWARD_CURRENCY[tier]
            if tier == 'normal':
                if self.rng.random() < ORB_DROP_CHANCE:
                    self.orbs.append(VitalityOrb(actor.x + actor.width / 2 - 10,
                                                actor.y + actor.height / 2))
            elif player is not None:
                heal(player, player.max_hp if tier == 'main' else MID_BOSS_HEAL)

    def update(self, dt, world, player):
        self.orbs = [orb for orb in self.orbs if not orb.update(dt, world, player)]
