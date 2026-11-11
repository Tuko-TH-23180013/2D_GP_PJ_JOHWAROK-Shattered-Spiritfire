"""장승마을 1지역 임시 지형. 그래픽과 배치는 추후 조정한다."""
from world import World, Rect
from enemy import Enemy


class VillageStage:
    width = 3200
    height = 720
    spawn = (120.0, 100.0)
    checkpoint_spawn = (2500.0, 100.0)
    boss_entrance = Rect(3000, 100, 3150, 300)
    regions = ((0, "Village entrance"), (280, "Platforms"),
               (900, "Village combat"), (2400, "Checkpoint"), (2900, "Boss gate"))

    def create_world(self):
        world = World([
            Rect(0, 0, self.width, 100), Rect(-40, 0, 0, self.height),
            Rect(self.width, 0, self.width + 40, self.height),
            Rect(0, self.height, self.width, self.height + 40),
            Rect(280, 210, 450, 235, True), Rect(530, 340, 710, 365, True),
            Rect(810, 470, 1010, 495, True), Rect(1070, 100, 1120, 270),
            Rect(1400, 200, 1600, 225, True), Rect(1760, 310, 1950, 335, True),
            Rect(2100, 200, 2300, 225, True),
        ])
        return world

    def create_enemies(self):
        return [Enemy(900, 100)]

    def region_at(self, x):
        return next(name for start, name in reversed(self.regions) if x >= start)
