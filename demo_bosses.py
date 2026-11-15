"""데모 보스 전용 행동. Boss의 스태거/다운/기상 규칙을 공유한다."""
from attack import Attack, AttackData
from boss import Boss
from monsters import DemoLife

SLASH = AttackData('Hahoe slash', .55, .15, .50, 18, 0, 130, 100)
THRUST = AttackData('Hahoe thrust', .40, .18, .40, 15, 0, 150, 70)


class DemoBoss(DemoLife, Boss):
    def begin_update(self, dt, player, world):
        if self.update_death(dt):
            return False
        if self.state in ('DOWN', 'WAKE') or player.hp <= 0:
            super().update(dt, player, world)
            return False
        return True

    def advance_pattern(self, dt, world, speed=0):
        if self.attack.phase == 'ACTIVE' and speed:
            old = self.x
            delta = self.attack.facing * speed * dt
            edge = self.x + (self.width + delta if delta > 0 else delta)
            supported = any(s.left <= edge <= s.right and abs(s.top - self.y) < 6 for s in world.solids)
            if supported:
                world.move_x(self, delta)
            if abs(self.x - old - delta) > 1e-6:
                self.attack.elapsed = self.attack.data.startup + self.attack.data.active
        self.attack.advance(dt)
        self.state = self.attack.phase
        if self.state == 'DONE':
            self.attack = None
            self.state = 'NORMAL'
            self.cooldown = .50


class Hahoe(DemoBoss):
    width, height = 58, 108

    def __init__(self, x=1000, y=100):
        super().__init__(x, y)
        self.init_demo('hahoe')
        self.max_hp = self.hp = 300
        self.stagger_limit = 90
        self.pattern = 'SLASH'

    def update(self, dt, player, world):
        if not self.begin_update(dt, player, world):
            return
        if self.attack:
            self.advance_pattern(dt, world, 210 if self.pattern == 'THRUST' else 0)
            return
        self.cooldown = max(0, self.cooldown - dt)
        if self.cooldown > 0:
            return
        dx = player.x + player.width / 2 - self.x - self.width / 2
        self.facing = 1 if dx >= 0 else -1
        if abs(dx) > 215:
            self.state = 'APPROACH'
            world.move_x(self, self.facing * 130 * dt)
            return
        self.pattern = 'SLASH' if abs(dx) <= 130 else 'THRUST'
        self.sheet = 'hahoe' if self.pattern == 'SLASH' else 'hahoe_thrust'
        self.attack = Attack(self, SLASH if self.pattern == 'SLASH' else THRUST)
        self.state = 'STARTUP'
