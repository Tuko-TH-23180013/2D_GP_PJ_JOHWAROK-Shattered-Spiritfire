"""일반 적 1종: 행동 AI만 담당하며 피해 판정은 CombatSystem에 맡긴다."""

from attack import Attack, AttackData
from world import Rect
from settings import GRAVITY, MAX_FALL_SPEED

# 스프라이트 및 밸런스 작업 전 임시값.
ENEMY_ATTACK = AttackData("Enemy swing", 0.45, 0.15, 0.45, 15, 0, 85, 65)


class Enemy:
    width, height = 44, 72

    def __init__(self, x=900.0, y=100.0):
        self.x, self.y = x, y
        self.team = "enemy"
        self.vy = 0.0
        self.facing = -1
        self.max_hp = self.hp = 120
        self.invulnerable = False
        self.stagger = 0
        self.stagger_limit = 60
        self.stagger_remaining = 0.0
        self.hit_flash = 0.0
        self.attack = None
        self.state = "IDLE"
        self.cooldown = 0.0

    @property
    def bounds(self):
        return Rect(self.x, self.y, self.x + self.width, self.y + self.height)

    def on_combat_hit(self):
        # 피해/스태거 계산은 CombatSystem이 수행한 뒤 행동만 정리한다.
        if self.hp <= 0:
            self.state, self.attack = "DEAD", None
        elif self.stagger_remaining > 0:
            self.state, self.attack = "STAGGER", None
            self.cooldown = 0.30

    def update(self, dt, player, world):
        if self.hp <= 0:
            self.state, self.attack = "DEAD", None
            return
        if player.hp <= 0:
            self.state, self.attack = "IDLE", None
            return
        self.cooldown = max(0.0, self.cooldown - dt)
        old_vy = self.vy
        self.vy = max(-MAX_FALL_SPEED, self.vy - GRAVITY * dt)
        _, hit = world.move_y(self, (old_vy + self.vy) * 0.5 * dt)
        if hit:
            self.vy = 0.0
        if self.stagger_remaining > 0:
            self.state, self.attack = "STAGGER", None
            return
        if self.attack is not None:
            self.attack.advance(dt)
            self.state = self.attack.phase
            if self.attack.phase == "DONE":
                self.attack = None
                self.cooldown = 0.30
                self.state = "IDLE"
            return
        dx = player.x + player.width / 2 - (self.x + self.width / 2)
        vertical_overlap = self.y < player.y + player.height and self.y + self.height > player.y
        if abs(dx) > 550 or not vertical_overlap:
            self.state = "IDLE"
            return
        self.facing = 1 if dx >= 0 else -1
        if abs(dx) > 95:
            self.state = "CHASE"
            world.move_x(self, self.facing * 110.0 * dt)
        elif self.cooldown <= 0:
            self.attack = Attack(self, ENEMY_ATTACK)
            self.state = "STARTUP"
        else:
            self.state = "IDLE"
