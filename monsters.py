"""제공된 데모 구상에 따른 7종 AI. 수치/배치는 밸런스 확정 전 임시값."""
from dataclasses import dataclass
from math import hypot

from attack import Attack, AttackData
from combat_system import overlaps
from enemy import Enemy
from monster_sprites import duration
from settings import GRAVITY, MAX_FALL_SPEED
from world import Rect

# 거대 방망이 1타→2타(최대 약 0.74초 간격)도 이어지는 임시 경직 시간.
NORMAL_HITSTUN = .80
EMBER_DETECTION_X = 640.0
EMBER_DETECTION_Y = 100.0  # 중심 간 높이 차이. 데모 인식 범위 임시값.


@dataclass(frozen=True)
class MonsterSpec:
    hp: int
    size: tuple
    speed: float
    distance: float
    attack: AttackData


SPECS = {
    'jangseung': MonsterSpec(90, (44, 72), 80, 100, AttackData('Wood slam', .45, .15, .45, 15, 0, 85, 72)),
    'sotdae': MonsterSpec(45, (44, 38), 80, 260, AttackData('Bird dive', .55, .55, .65, 12, 0, 34, 45)),
    'ember': MonsterSpec(45, (38, 40), 65, 430, AttackData('Spiritfire shot', .60, .12, .65, 12, 0, 0, 0)),
    'mask': MonsterSpec(60, (40, 60), 120, 190, AttackData('Mask leap', .40, .65, .40, 13, 0, 50, 60)),
    'onggi': MonsterSpec(100, (48, 58), 60, 100, AttackData('Pot headbutt', .55, .18, .55, 17, 0, 75, 60)),
    'rice_chest': MonsterSpec(80, (54, 58), 45, 150, AttackData('Rice burst', .65, .18, .60, 14, 0, 135, 70)),
    'jige': MonsterSpec(100, (46, 76), 85, 290, AttackData('Log charge', .70, .55, .65, 18, 0, 55, 78)),
}


class Spiritfire(Attack):
    """공격자와 분리된 단발 투사체. 동일 CombatSystem에 판정을 맡긴다."""
    width, height = 24, 18

    def __init__(self, owner):
        super().__init__(owner, AttackData('Spiritfire', 0, 2.5, 0, 12, 0, 24, 18))
        self.x = owner.x + (owner.width if self.facing > 0 else -self.width)
        self.y = owner.y + owner.height / 2 - self.height / 2

    @property
    def bounds(self):
        return Rect(self.x, self.y, self.x + self.width, self.y + self.height)

    def update(self, dt, world):
        self.advance(dt)
        old = self.x
        distance = self.facing * 310 * dt
        world.move_x(self, distance)
        if (abs(self.x - old - distance) > 1e-6 or self.owner.hp <= 0
                or self.hit_targets or any(overlaps(self.bounds, s) for s in world.solids if not s.one_way)):
            self.elapsed = self.data.active


class DemoLife:
    """사망 시 좌표/방향을 동결하고 시트를 한 번 재생한 후 제거한다."""
    def init_demo(self, kind):
        self.kind = self.sheet = kind
        self.death_age = 0.0
        self.projectiles = []

    @property
    def death_done(self):
        return self.hp <= 0 and self.death_age >= duration(self.kind + '_death')

    def update_death(self, dt):
        if self.hp > 0:
            return False
        self.state, self.attack = 'DEAD', None
        self.projectiles.clear()
        self.vy = 0
        self.death_age += dt
        return True


class Monster(DemoLife, Enemy):
    def __init__(self, kind, x, y=100):
        super().__init__(x, y)
        self.init_demo(kind)
        self.spec = SPECS[kind]
        self.width, self.height = self.spec.size
        self.max_hp = self.hp = self.spec.hp
        self.flying = kind in ('sotdae', 'ember')
        self.home_y = y
        self.triggered = False
        self.dive_velocity = (0, 0)
        self.hitstun_remaining = 0.0

    def on_combat_hit(self):
        super().on_combat_hit()
        if self.hp <= 0:
            self.projectiles.clear()
            self.hitstun_remaining = 0.0
        else:
            self.hitstun_remaining = NORMAL_HITSTUN
            self.state, self.attack = 'HURT', None
            self.projectiles.clear()  # 아직 게임으로 전달하지 않은 발사는 취소한다.
            self.vy = min(0, self.vy)

    def supported_ahead(self, world, distance):
        edge = self.x + (self.width + distance if distance >= 0 else distance)
        return any(s.left <= edge <= s.right and abs(s.top - self.y) < 6 for s in world.solids)

    def move_ground(self, world, distance):
        old = self.x
        if self.supported_ahead(world, distance):
            world.move_x(self, distance)
        return abs(self.x - old - distance) < 1e-6

    def recover(self):
        if self.attack:
            self.attack.elapsed = self.attack.data.startup + self.attack.data.active

    def detects_player(self, player):
        dx = player.x + player.width / 2 - self.x - self.width / 2
        dy = player.y + player.height / 2 - self.y - self.height / 2
        return (player.hp > 0 and abs(dx) <= EMBER_DETECTION_X
                and abs(dy) <= EMBER_DETECTION_Y)

    def update(self, dt, player, world):
        if self.update_death(dt):
            return
        if player.hp <= 0:
            self.attack = None
            self.projectiles.clear()
            return
        landed = False
        if not self.flying:
            old_vy = self.vy
            self.vy = max(-MAX_FALL_SPEED, self.vy - GRAVITY * dt)
            landed, hit = world.move_y(self, (old_vy + self.vy) * .5 * dt)
            if hit:
                self.vy = 0
        self.cooldown = max(0, self.cooldown - dt)
        if self.hitstun_remaining > 0:
            self.hitstun_remaining = max(0, self.hitstun_remaining - dt)
            self.state, self.attack = 'HURT', None
            return
        if self.stagger_remaining > 0:
            self.state, self.attack = 'STAGGER', None
            return
        if self.kind == 'ember' and not self.detects_player(player):
            # 공격 시작뿐 아니라 발사 직전에도 현재 위치의 인식 여부를 확인한다.
            if self.attack is not None:
                self.cooldown = max(self.cooldown, .5)
            self.state, self.attack = 'IDLE', None
            self.triggered = False
            return
        if self.attack:
            self.attack.advance(dt)
            if self.attack.phase == 'ACTIVE':
                if not self.triggered:
                    self.triggered = True
                    if self.kind == 'ember':
                        self.projectiles.append(Spiritfire(self))
                    elif self.kind == 'mask':
                        self.vy = 350
                        landed = False
                if self.kind == 'sotdae':
                    old_x = self.x
                    vx, vy = self.dive_velocity
                    world.move_x(self, vx * dt)
                    _, hit = world.move_y(self, vy * dt)
                    if hit or abs(self.x - old_x - vx * dt) > 1e-6:
                        self.recover()
                elif self.kind == 'mask':
                    world.move_x(self, self.attack.facing * 260 * dt)
                    if landed:
                        self.recover()
                elif self.kind in ('jige', 'onggi'):
                    speed = 390 if self.kind == 'jige' else 180
                    if not self.move_ground(world, self.attack.facing * speed * dt):
                        self.recover()
            self.state = self.attack.phase
            if self.state == 'DONE':
                self.attack = None
                self.cooldown = .5
                self.state = 'IDLE'
            return
        if self.flying and abs(self.y - self.home_y) > 1:
            world.move_y(self, max(-100 * dt, min(100 * dt, self.home_y - self.y)))
        dx = player.x + player.width / 2 - self.x - self.width / 2
        dy = player.y + player.height / 2 - self.y - self.height / 2
        if abs(dx) > 640:
            self.state = 'IDLE'
            return
        self.facing = 1 if dx >= 0 else -1
        if abs(dx) > self.spec.distance:
            self.state = 'CHASE'
            distance = self.facing * self.spec.speed * dt
            if self.flying:
                world.move_x(self, distance)
            else:
                self.move_ground(world, distance)
        elif self.cooldown <= 0 and (self.flying or abs(dy) < 100):
            self.attack = Attack(self, self.spec.attack)
            self.triggered = False
            # 급강하는 준비 시작 시 목표를 고정한다. 이후 플레이어를 추적하지 않는다.
            length = max(1, hypot(dx, dy))
            self.dive_velocity = (dx / length * 430, dy / length * 430)
            self.state = 'STARTUP'
        else:
            self.state = 'IDLE'
