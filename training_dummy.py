"""공격 AI가 없는 3단계 연습 대상. R 입력으로 새 대상으로 교체한다."""

from world import Rect


class TrainingDummy:
    def __init__(self, x=420, y=100):
        self.x, self.y = x, y
        self.width, self.height = 48, 90
        self.max_hp = self.hp = 200
        self.stagger = 0
        self.stagger_limit = 60
        self.stagger_remaining = 0.0
        self.hit_flash = 0.0
        self.invulnerable = False

    @property
    def bounds(self):
        return Rect(self.x, self.y, self.x + self.width, self.y + self.height)
