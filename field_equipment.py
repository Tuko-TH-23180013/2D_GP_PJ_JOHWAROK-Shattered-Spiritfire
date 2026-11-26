"""필드 아이템 일회 처리, F 유지 입력, 장비창 상태. 상점 거래는 포함하지 않는다."""
from dataclasses import dataclass
from itertools import count
import random
import sdl2
from equipment import ITEMS, Equipment
import growth_settings as cfg

_ids = count()


@dataclass(eq=False)
class Drop:
    item_id: str
    x: float
    y: float
    source: str = 'reward'
    consumed: bool = False
    width: float = 24
    height: float = 24
    vy: float = 0

    def __post_init__(self):
        self.uid = next(_ids)

    def update(self, dt, world):
        self.vy = max(-600, self.vy - 900 * dt)
        if world.move_y(self, self.vy * dt)[1]:
            self.vy = 0


class FieldEquipment:
    def __init__(self):
        self.equipment = Equipment()
        self.unlocked_forms = ('basic', 'giant')  # 기존 두 폼, 영구 구매/저장은 후속.
        self.special_claimed = False
        self.rng = random.Random()
        self.reset_room()

    def reset_room(self):
        self.drops = []
        self.chests = []
        self.chest_open = None
        self.rewarded = set()
        self.open = False
        self.pending = None
        self.reset_hold()

    def reset_hold(self):
        self.hold_target = None
        self.hold_time = 0

    def toggle(self):
        self.open = not self.open
        self.pending = None
        self.reset_hold()

    def add_drop(self, item_id, player, source='equipment'):
        drop = Drop(item_id, player.x + player.width / 2 - 12, player.y, source)
        self.drops.append(drop)
        return drop

    def nearest(self, player):
        available = [d for d in self.drops if not d.consumed
                     and abs(d.x - player.x) <= cfg.INTERACTION_DISTANCE
                     and abs(d.y - player.y) <= cfg.INTERACTION_DISTANCE]
        return min(available, key=lambda d: abs(d.x-player.x)+abs(d.y-player.y), default=None)

    def nearest_chest(self, player):
        nearby = [c for c in self.chests if not c.claimed
                  and abs(c.x-player.x) <= cfg.INTERACTION_DISTANCE
                  and abs(c.y-player.y) <= cfg.INTERACTION_DISTANCE]
        return min(nearby, key=lambda c: abs(c.x-player.x)+abs(c.y-player.y), default=None)

    def take(self, drop, player):
        if drop.consumed or drop not in self.drops:
            return False
        if None not in self.equipment.slots:
            self.pending = drop
            self.open = True
            self.reset_hold()
            return False
        self.equipment.equip(self.equipment.slots.index(None), drop.item_id)
        drop.consumed = True
        player.refresh_stats()
        return True

    def replace(self, slot, player):
        if not self.open:
            return
        drop = self.pending
        if drop is not None and (drop.consumed or drop not in self.drops):
            self.pending = None
            return
        old = self.equipment.equip(slot, drop.item_id if drop else None)
        if old:
            self.add_drop(old, player)
        if drop:
            drop.consumed = True
        self.pending = None
        player.refresh_stats()

    def update_field(self, game, dt):
        """True면 이번 입력을 아이템이 처리하여 출구 등으로 전파하지 않는다."""
        player, inputs = game.player, game.inputs
        for drop in self.drops:
            if not drop.consumed:
                drop.update(dt, game.world)
        target = self.nearest(player)
        chest = self.nearest_chest(player)
        if chest and (target is None or abs(chest.x-player.x) < abs(target.x-player.x)):
            self.reset_hold()
            if sdl2.SDLK_f in inputs.pressed:
                self.chest_open = chest
            return True
        if inputs.focus_lost or target is not self.hold_target:
            self.reset_hold()
        if sdl2.SDLK_f in inputs.pressed and target:
            if target.item_id not in self.equipment.slots:
                self.take(target, player)
                return True
            self.hold_target = target
        if self.hold_target is not None:
            target = self.hold_target
            if sdl2.SDLK_f in inputs.held:
                self.hold_time += dt
                if self.hold_time + 1e-9 >= cfg.HOLD_SECONDS:
                    if not target.consumed:
                        target.consumed = True
                        game.rewards.balance += cfg.CONVERT_GOLD
                    self.reset_hold()
            elif sdl2.SDLK_f in inputs.released:
                self.take(target, player)
                self.reset_hold()
            else:
                self.reset_hold()
            return True
        return target is not None

    def award(self, game):
        for index in range(game.encounters.completed):
            if index not in self.rewarded:
                self.rewarded.add(index)
                from reward_chest import RewardChest
                x = game.encounters.zones[index].gate_x
                self.chests.append(RewardChest('item', (self.rng.choice(tuple(ITEMS)),), x-180))
                if game.room_index == 0 and index == 0 and not self.special_claimed:
                    self.chests.append(RewardChest('ability', ('enlarge', 'blink'), x-70))

    def can_change_form(self, game):
        return (game.player.hp > 0 and game.encounters.finished
                and not game.enemies and (game.boss is None or game.boss.death_done)
                and not game.projectiles and game.player.attack is None
                and game.player.dash_remaining <= 1e-9
                and game.player.switch_remaining <= 1e-9)

    def select_form(self, game, form):
        if self.open and form in self.unlocked_forms and self.can_change_form(game):
            game.player.weapon = form
            return True
        return False
