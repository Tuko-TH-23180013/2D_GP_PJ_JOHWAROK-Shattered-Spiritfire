"""맵 내부 전투 구역 진행. 적 AI/피해와 분리된 일회성 생성·봉쇄 상태."""
from monsters import Monster
from world import Rect


class EncounterFlow:
    def __init__(self, zones, world):
        self.zones = zones
        self.completed = 0
        self.next_index = 0
        self.active_index = None
        self.gate = None
        if zones:
            # 첫 구역의 적은 Room.create_enemies가 이미 생성한다.
            self.activate(0, world)

    @property
    def finished(self):
        return self.completed == len(self.zones)

    def activate(self, index, world):
        zone = self.zones[index]
        self.active_index = index
        self.next_index = index + 1
        self.gate = Rect(zone.gate_x, 100, zone.gate_x + 16, 720)
        world.solids.append(self.gate)

    def update(self, player, enemies, world):
        if player.hp <= 0:
            return []
        # 사망 애니메이션까지 재생한 뒤 enemies에서 제거되어야 길이 열린다.
        if self.active_index is not None and not enemies:
            world.solids.remove(self.gate)
            self.gate = None
            self.active_index = None
            self.completed += 1
        if self.active_index is None and self.next_index < len(self.zones):
            zone = self.zones[self.next_index]
            if player.x + player.width >= zone.trigger_x:
                self.activate(self.next_index, world)
                return [Monster(kind, x, y) for kind, x, y in zone.spawns]
        return []
