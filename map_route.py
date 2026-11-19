"""사용자 요청에 따른 7개 임시 맵. 배치/적 수는 밸런스 조정 전 데이터."""
from dataclasses import dataclass
from world import World, Rect
from monsters import Monster
from demo_bosses import Hahoe, Guardian


@dataclass(frozen=True)
class Encounter:
    trigger_x: float
    gate_x: float
    spawns: tuple


@dataclass(frozen=True)
class Room:
    name: str
    category: str
    width: int
    spawns: tuple = ()
    platforms: tuple = ()
    camera_zoom: float = 0.9  # 참고 이미지의 캐릭터 높이 약 9~10% 기준.
    encounters: tuple = ()
    sections: tuple = ()

    @property
    def regions(self):
        return self.sections or ((0, self.name),)

    @property
    def boss_entrance(self):
        return Rect(self.width - 130, 100, self.width - 40, 280)

    def region_at(self, x):
        return next((name for start, name in reversed(self.regions) if x >= start), self.name)

    def create_world(self):
        return World([Rect(0, 0, self.width, 100), Rect(-40, 0, 0, 720),
                      Rect(self.width, 0, self.width + 40, 720),
                      Rect(0, 720, self.width, 760), *self.platforms])

    def create_enemies(self):
        return [Monster(kind, x, y) for kind, x, y in self.spawns]

    def create_boss(self):
        if self.category == 'mid':
            return Hahoe(1000)
        if self.category == 'main':
            return Guardian(1100)
        return None


def combat_room(name, width, first, second, platforms):
    """진입→전투→발판 이동→혼합 전투→출구. 지상 주 경로는 항상 연결한다."""
    return Room(name, 'normal', width, first, platforms,
                encounters=(Encounter(0, 1350, first), Encounter(1750, width - 350, second)),
                sections=((0, 'Approach'), (450, 'Battle 1'), (1400, 'Traversal'),
                          (1750, 'Battle 2'), (width - 300, 'Exit path')))


ROOMS = (
    combat_room('Village approach', 3200,
                (('jangseung', 550, 100), ('mask', 850, 100)),
                (('mask', 2050, 100), ('jangseung', 2350, 100)),
                (Rect(700, 210, 930, 230, True), Rect(1420, 200, 1590, 220, True),
                 Rect(1620, 300, 1830, 320, True), Rect(2180, 220, 2440, 240, True))),
    combat_room('Pottery lane', 3400,
                (('onggi', 550, 100), ('sotdae', 950, 210)),
                (('onggi', 2100, 100), ('sotdae', 2450, 210)),
                (Rect(740, 220, 1000, 240, True), Rect(1420, 210, 1600, 230, True),
                 Rect(1640, 320, 1850, 340, True), Rect(2240, 230, 2490, 250, True),
                 Rect(2650, 330, 2880, 350, True))),
    Room('Hahoe courtyard', 'mid', 1600),
    Room('Spiritfire sanctuary', 'save', 1280),
    combat_room('Abandoned granary', 3500,
                (('ember', 600, 120), ('rice_chest', 1050, 100)),
                (('mask', 2050, 100), ('ember', 2370, 120), ('rice_chest', 2700, 100)),
                (Rect(780, 210, 1030, 230, True), Rect(1420, 200, 1600, 220, True),
                 Rect(1650, 305, 1850, 325, True), Rect(2200, 215, 2460, 235, True),
                 Rect(2630, 310, 2860, 330, True))),
    combat_room('Forest barricade', 3600,
                (('jige', 650, 100), ('jangseung', 1050, 100)),
                (('jige', 2100, 100), ('mask', 2440, 100), ('jangseung', 2800, 100)),
                (Rect(800, 230, 1100, 250, True), Rect(1420, 210, 1600, 230, True),
                 Rect(1660, 330, 1860, 350, True), Rect(2260, 240, 2520, 260, True),
                 Rect(2720, 240, 3010, 260, True))),
    Room('Corrupted guardian shrine', 'main', 1700),
)
