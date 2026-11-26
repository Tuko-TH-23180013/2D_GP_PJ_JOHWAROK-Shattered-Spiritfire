"""보상 생성과 수령을 분리한다. 후보는 상자 생성 때 결정하며 재열기로 바뀌지 않는다."""
from dataclasses import dataclass


@dataclass(eq=False)
class RewardChest:
    kind: str
    choices: tuple
    x: float
    y: float = 100
    claimed: bool = False
    selected: int | None = None

    def claim(self, game):
        gear = game.gear
        if self.claimed or gear.chest_open is not self or self.selected is None:
            return False
        if not 0 <= self.selected < len(self.choices):
            return False
        chosen = self.choices[self.selected]
        if self.kind == 'ability':
            if gear.special_claimed:
                return False
            game.abilities.owned.add(chosen)
            game.abilities.equip(chosen)
            gear.special_claimed = True
        else:
            drop = gear.add_drop(chosen, game.player, 'chest')
            # 기존 보유 중복은 바닥에 남겨 F 획득/전환 선택을 유지한다.
            if chosen not in gear.equipment.slots:
                gear.take(drop, game.player)
        self.claimed = True
        gear.chest_open = None
        gear.reset_hold()
        return True
