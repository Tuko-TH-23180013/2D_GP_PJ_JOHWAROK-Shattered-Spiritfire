"""사용자 요청에 따른 7개 임시 맵. 배치/적 수는 밸런스 조정 전 데이터."""
from dataclasses import dataclass
from world import World, Rect
from monsters import Monster
from demo_bosses import Hahoe, Guardian


@dataclass(frozen=True)
class Room:
    name: str
    category: str
    width: int
    spawns: tuple = ()
    platforms: tuple = ()

    @property
    def regions(self):
        return ((0, self.name),)

    @property
    def boss_entrance(self):
        return Rect(self.width - 130, 100, self.width - 40, 280)

    def region_at(self, x):
        return self.name

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


ROOMS = (
    Room('Village approach', 'normal', 1800,
         (('jangseung', 550, 100), ('mask', 1120, 100)),
         (Rect(700, 220, 900, 240, True),)),
    Room('Pottery lane', 'normal', 1900,
         (('onggi', 550, 100), ('sotdae', 1200, 210)),
         (Rect(850, 230, 1050, 250, True), Rect(1300, 300, 1480, 320, True))),
    Room('Hahoe courtyard', 'mid', 1600),
    Room('Spiritfire sanctuary', 'save', 1280),
    Room('Abandoned granary', 'normal', 1900,
         (('ember', 600, 120), ('rice_chest', 1200, 100)),
         (Rect(850, 215, 1050, 235, True),)),
    Room('Forest barricade', 'normal', 1900,
         (('jige', 650, 100), ('jangseung', 1250, 100)),
         (Rect(900, 240, 1100, 260, True),)),
    Room('Corrupted guardian shrine', 'main', 1700),
)
