"""현재 실행 중에만 유지되는 장승 체크포인트."""


class Checkpoint:
    def __init__(self, spawn):
        self.spawn = spawn
        self.active = False

    def can_activate(self, player):
        x, y = self.spawn
        return (player.hp > 0 and player.grounded
                and abs(player.x + player.width / 2 - x) <= 80
                and abs(player.y - y) <= 8)

    def activate(self, player):
        if self.can_activate(player):
            self.active = True
            return True
        return False
