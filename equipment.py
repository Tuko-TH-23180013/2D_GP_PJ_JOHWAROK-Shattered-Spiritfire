"""장착 아이템과 각인 집계. 저장된 최종 스탯에 보정을 누적하지 않는다."""
from dataclasses import dataclass
from collections import Counter
import growth_settings as cfg


@dataclass(frozen=True)
class Stats:
    attack: float = 0
    hp: int = 0
    reduction: float = 0
    stagger: float = 0


@dataclass(frozen=True)
class Item:
    name: str
    inscription: str
    stats: Stats


# 문서의 후보 9개를 시험용으로 사용한다.
ITEMS = {
    'fang': Item('금 간 도깨비 어금니', '맹공', Stats(attack=.05)),
    'red_knot': Item('붉은 매듭', '맹공', Stats(hp=10)),
    'talisman': Item('낡은 전투 부적', '맹공', Stats(stagger=.05)),
    'iron_ring': Item('오래된 철고리', '파쇄', Stats(stagger=.10)),
    'weight': Item('무거운 장식추', '파쇄', Stats(attack=.05)),
    'stone': Item('금 간 돌패', '파쇄', Stats(hp=10)),
    'guard_knot': Item('수호 매듭', '수호', Stats(hp=15)),
    'mirror': Item('작은 호신경', '수호', Stats(reduction=.05)),
    'bell': Item('푸른 방울', '수호', Stats(attack=.05)),
}
BONUSES = {'맹공': Stats(attack=.10), '수호': Stats(reduction=.10),
           '파쇄': Stats(stagger=.20)}


class Equipment:
    def __init__(self):
        self.slots = [None] * cfg.EQUIPMENT_SLOTS

    def equip(self, slot, item_id):
        if item_id is not None and item_id not in ITEMS:
            raise ValueError(item_id)
        old = self.slots[slot]
        self.slots[slot] = item_id
        return old

    def counts(self):
        ids = [item for item in self.slots if item is not None]
        return Counter(ITEMS[item].inscription for item in
                       (ids if cfg.COUNT_DUPLICATES else set(ids)))

    def calculate(self):
        effects = [ITEMS[item].stats for item in self.slots if item is not None]
        effects += [BONUSES[name] for name, count in self.counts().items()
                    if count >= cfg.INSCRIPTION_THRESHOLD]
        return Stats(**{field: sum(getattr(effect, field) for effect in effects)
                        for field in Stats.__dataclass_fields__})
