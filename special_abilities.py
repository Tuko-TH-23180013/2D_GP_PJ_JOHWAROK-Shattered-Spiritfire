"""능력별 독립 타이머. 발동 조건·이동 판정은 표시와 분리한다."""
import growth_settings as cfg
from types import SimpleNamespace

NAMES = {'enlarge': '거대화', 'blink': '축지'}


class Abilities:
    def __init__(self):
        self.equipped = None
        self.owned = set()
        self.cooldowns = {key: 0.0 for key in NAMES}
        self.giant_remaining = 0.0

    def equip(self, name):
        if name not in self.owned:
            return False
        self.equipped = name
        return True

    def blink_destination(self, player, world):
        probe = SimpleNamespace(x=player.x, y=player.y, width=player.width, height=player.height)
        world.move_x(probe, player.facing * cfg.BLINK_DISTANCE)
        if any(probe.x < s.right and probe.x+probe.width > s.left
               and probe.y < s.top and probe.y+probe.height > s.bottom for s in world.solids):
            return player.x
        return probe.x

    def available(self, player, world=None):
        return (self.equipped is not None and player.hp > 0
                and self.cooldowns[self.equipped] <= 1e-9
                and player.attack is None and player.dash_remaining <= 1e-9
                and player.switch_remaining <= 1e-9
                and (self.equipped != 'blink' or world is None
                     or abs(self.blink_destination(player, world)-player.x) > 1e-9)
                and not (self.equipped == 'enlarge' and self.giant_remaining > 1e-9))

    def use(self, player, world):
        if not self.available(player, world):
            return False
        if self.equipped == 'enlarge':
            self.giant_remaining = cfg.GIANT_DURATION
            self.cooldowns['enlarge'] = cfg.GIANT_COOLDOWN
        else:
            before = player.x
            # 경로의 벽/결계를 넘지 않는 가장 가까운 안전 위치. 추가 무적 없음.
            player.x = self.blink_destination(player, world)
            if abs(player.x - before) < 1e-9:
                return False
            self.cooldowns['blink'] = cfg.BLINK_COOLDOWN
        player.refresh_stats()
        return True

    def update(self, dt):
        for name in self.cooldowns:
            self.cooldowns[name] = max(0.0, self.cooldowns[name] - dt)
        self.giant_remaining = max(0.0, self.giant_remaining - dt)
