"""능력별 독립 타이머. 발동 조건·이동 판정은 표시와 분리한다."""
import growth_settings as cfg
from math import hypot

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

    def blink_destination(self, player, world, direction=(0, 0)):
        dx, dy = direction
        length = hypot(dx, dy)
        if length <= 1e-9:
            dx, dy, length = player.facing, 0, 1
        dx, dy = dx/length*cfg.BLINK_DISTANCE, dy/length*cfg.BLINK_DISTANCE
        x, y = world.sweep_position(player, dx, dy, player.drop_platforms)
        # 아래에서 통과 가능한 발판도 그 두께 내부에 도착하는 것은 허용하지 않는다.
        if any(x < s.right-1e-8 and x+player.width > s.left+1e-8
               and y < s.top-1e-8 and y+player.height > s.bottom+1e-8 for s in world.solids):
            return player.x, player.y
        return x, y

    def available(self, player, world=None, direction=(0, 0)):
        return (self.equipped is not None and player.hp > 0
                and self.cooldowns[self.equipped] <= 1e-9
                and player.attack is None and player.dash_remaining <= 1e-9
                and player.switch_remaining <= 1e-9
                and (self.equipped != 'blink' or world is None
                     or hypot(*(a-b for a, b in zip(self.blink_destination(player, world, direction),
                                                    (player.x, player.y)))) > 1e-9)
                and not (self.equipped == 'enlarge' and self.giant_remaining > 1e-9))

    def use(self, player, world, direction=(0, 0)):
        if not self.available(player, world, direction):
            return False
        if self.equipped == 'enlarge':
            self.giant_remaining = cfg.GIANT_DURATION
            self.cooldowns['enlarge'] = cfg.GIANT_COOLDOWN
        else:
            # 경로의 벽/결계를 넘지 않는 가장 가까운 안전 위치. 추가 무적 없음.
            player.x, player.y = self.blink_destination(player, world, direction)
            supports = [s for s in world.solids if s not in player.drop_platforms
                        and abs(player.y-s.top) < 1e-7
                        and player.x < s.right and player.x+player.width > s.left]
            player.grounded = bool(supports)
            if supports:
                player.vy = 0
                player.jumps_used = 0
            else:
                player.jumps_used = max(1, player.jumps_used)
                if player.vy > 0 and any(not s.one_way and abs(player.y+player.height-s.bottom) < 1e-7
                                        and player.x < s.right and player.x+player.width > s.left
                                        for s in world.solids):
                    player.vy = 0
            self.cooldowns['blink'] = cfg.BLINK_COOLDOWN
        player.refresh_stats()
        return True

    def update(self, dt):
        for name in self.cooldowns:
            self.cooldowns[name] = max(0.0, self.cooldowns[name] - dt)
        self.giant_remaining = max(0.0, self.giant_remaining - dt)
