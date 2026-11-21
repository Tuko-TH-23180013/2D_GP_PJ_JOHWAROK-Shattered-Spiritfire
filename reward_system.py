"""처치 보상. 강화용 혼불은 현재 실행 세션 동안 유지한다."""

REWARD_CURRENCY = {'normal': 5, 'mid': 50, 'main': 150}  # 임시 밸런스


class RewardSystem:
    def __init__(self):
        self.balance = 0
        self.reset_room()

    def reset_room(self):
        # 객체 자체를 보관하여 제거된 적의 id 재사용도 방지한다.
        self.credited = set()

    def collect_defeats(self, actors, boss=None, category='normal'):
        for actor in actors:
            if actor.hp > 0 or actor in self.credited:
                continue
            self.credited.add(actor)
            tier = category if actor is boss else 'normal'
            self.balance += REWARD_CURRENCY[tier]
