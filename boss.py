"""오래된 도깨비의 임시 두 패턴. 피해 계산은 CombatSystem 담당."""
from attack import Attack, AttackData
from enemy import Enemy

SWING = AttackData("Boss swing", 0.65, 0.18, 0.60, 22, 0, 170, 110)
RUSH = AttackData("Boss rush", 0.85, 0.55, 0.75, 28, 0, 95, 105)


class Boss(Enemy):
    width, height = 96, 120

    def __init__(self, x=3950.0, y=100.0):
        super().__init__(x, y)
        self.max_hp = self.hp = 500
        self.stagger_limit = 120
        self.pattern_index = 0
        self.pattern = "SWING"
        self.state = "NORMAL"
        self.cooldown = 0.5

    def on_combat_hit(self):
        if self.hp <= 0:
            self.state, self.attack = "DEAD", None

    def update(self, dt, player, world):
        if self.hp <= 0:
            self.state, self.attack = "DEAD", None
            return
        if player.hp <= 0:
            self.attack = None
            return
        if self.attack is not None:
            if self.pattern == "RUSH" and self.attack.phase == "ACTIVE":
                world.move_x(self, self.attack.facing * 600 * dt)
            self.attack.advance(dt)
            self.state = self.attack.phase
            if self.state == "DONE":
                self.attack = None
                self.state = "NORMAL"
                self.cooldown = 0.45
            return
        self.cooldown = max(0.0, self.cooldown - dt)
        if self.cooldown > 0:
            return
        dx = player.x + player.width / 2 - (self.x + self.width / 2)
        self.facing = 1 if dx >= 0 else -1
        self.pattern = "SWING" if self.pattern_index % 2 == 0 else "RUSH"
        if self.pattern == "SWING" and abs(dx) > 190:
            world.move_x(self, self.facing * 130 * dt)
            self.state = "APPROACH"
            return
        data = SWING if self.pattern == "SWING" else RUSH
        self.attack = Attack(self, data)
        self.pattern_index += 1
        self.state = "STARTUP"
