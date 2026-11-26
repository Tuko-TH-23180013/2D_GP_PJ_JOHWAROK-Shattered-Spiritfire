"""처치 드롭과 회복. 골드는 판 단위, 획득 옥석은 실행 세션 동안 유지한다."""

from dataclasses import dataclass
import random
from math import hypot

REWARD_CURRENCY = {'normal': 5, 'mid': 50, 'main': 150}  # 임시 밸런스
REWARD_JADE = {'normal': 1, 'mid': 10, 'main': 30}  # 폼 성장용 옥석 시험값
ORB_DROP_CHANCE = .25
ORB_HEAL = 20
MID_BOSS_HEAL = 40
CURRENCY_BURST_SECONDS = .45
CURRENCY_ATTRACT_SPEED = 1400
CURRENCY_PIECES = {'normal': 1, 'mid': 3, 'main': 5}


@dataclass
class CurrencyDrop:
    kind: str
    amount: int
    x: float
    y: float
    vx: float
    vy: float
    age: float = 0
    width: float = 12
    height: float = 12

    def update(self, dt, world, player):
        if player.hp <= 0:
            return False
        burst = min(dt, max(0, CURRENCY_BURST_SECONDS-self.age))
        if burst:
            world.move_x(self, self.vx*burst)
            self.vy -= 700*burst
            if world.move_y(self, self.vy*burst)[1]:
                self.vy = max(0, -self.vy*.3)
            self.age += burst
        remaining = dt-burst
        if remaining <= 0:
            return False
        # 재화 흡수 연출은 충돌 물체가 아니다. 획득 불가능한 곳에 남지 않도록 자동 회수한다.
        dx, dy = player.x+player.width/2-self.x, player.y+player.height/2-self.y
        distance = hypot(dx,dy)
        travel = CURRENCY_ATTRACT_SPEED*remaining
        if distance <= travel+8:
            return True
        self.x += dx/distance*travel
        self.y += dy/distance*travel
        self.age += remaining
        return False


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
        self.gold = 0
        self.jade = 0
        self.reset_room()

    def reset_run(self):
        self.gold = 0
        self.reset_room()  # 획득한 옥석은 사망·새 판에도 유지한다.

    def reset_room(self):
        # 객체 자체를 보관하여 제거된 적의 id 재사용도 방지한다.
        self.credited = set()
        self.orbs = []
        self.currency_drops = []

    def credit(self, drop):
        if drop.kind == 'gold':
            self.gold += drop.amount
        else:
            self.jade += drop.amount

    def bank_pending(self):
        """살아 있는 플레이어의 맵 전환 시 회수 중 재화 유실 방지."""
        for drop in self.currency_drops:
            self.credit(drop)
        self.currency_drops.clear()

    def spawn_currency(self, actor, tier):
        for kind,total in (('gold',REWARD_CURRENCY[tier]),('jade',REWARD_JADE[tier])):
            pieces = min(total,CURRENCY_PIECES[tier])
            for i in range(pieces):
                amount = total//pieces + int(i < total%pieces)
                vx = (i-(pieces-1)/2)*75 + (-45 if kind == 'gold' else 45)
                self.currency_drops.append(CurrencyDrop(kind,amount,
                    actor.x+actor.width/2-6,actor.y+actor.height/2,vx,180+20*i))

    def collect_defeats(self, actors, boss=None, category='normal', player=None):
        for actor in actors:
            if actor.hp > 0 or actor in self.credited:
                continue
            self.credited.add(actor)
            tier = category if actor is boss else 'normal'
            self.spawn_currency(actor,tier)
            if tier == 'normal':
                if self.rng.random() < ORB_DROP_CHANCE:
                    self.orbs.append(VitalityOrb(actor.x + actor.width / 2 - 10,
                                                actor.y + actor.height / 2))
            elif player is not None:
                heal(player, player.max_hp if tier == 'main' else MID_BOSS_HEAL)

    def update(self, dt, world, player):
        self.orbs = [orb for orb in self.orbs if not orb.update(dt, world, player)]
        pending = []
        for drop in self.currency_drops:
            if drop.update(dt,world,player):
                self.credit(drop)
            else:
                pending.append(drop)
        self.currency_drops = pending
