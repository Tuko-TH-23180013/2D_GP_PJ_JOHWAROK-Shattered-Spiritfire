"""제공 시트의 프레임 선택과 좌표 변환. 전투/이동 상태는 변경하지 않는다."""
from pathlib import Path

ASSET_ROOT = (Path(__file__).resolve().parent / "Sprite_sheet"
              / "JOHWAROK_main_Sprite_Demo" / "assets")
CELL = 160
ROWS = COLUMNS = 5
FOOT_PIVOT = (80, 133)  # PNG 좌상단 기준.
HERO_SCALE = 0.9  # 기존 충돌 크기를 유지하는 임시 외형 배율.
GROUND_FRAMES = ((10, 11, 12), (13, 14, 15), (16, 17, 18))
GIANT_FRAMES = ((22, 23, 24), (16, 23, 18))  # 제공 데모의 2타 조합.


def source_rect(frame):
    if not 0 <= frame < ROWS * COLUMNS:
        raise ValueError(f"시트 프레임 범위 초과: {frame}")
    return frame % COLUMNS * CELL, (ROWS - 1 - frame // COLUMNS) * CELL, CELL, CELL


def draw_center(player, camera_x=0):
    return (player.x + player.width / 2 - camera_x,
            player.y + (FOOT_PIVOT[1] - CELL / 2) * HERO_SCALE * getattr(player, 'body_scale', 1))


class HeroAnimation:
    def __init__(self):
        self.clock = 0.0
        self.walk_clock = 0.0
        self.frame = 0

    def update(self, player, dt, previous_x):
        if player.hp <= 0:
            return  # 전용 사망 프레임이 없으므로 마지막 포즈 유지.
        self.clock += dt
        attack = player.attack
        if attack is not None:
            phase = {"STARTUP": 0, "ACTIVE": 1, "RECOVERY": 2, "DONE": 2}[attack.phase]
            frames = ((19, 20, 21) if attack.airborne else
                      GIANT_FRAMES[attack.combo_index] if player.weapon == "giant" else
                      GROUND_FRAMES[attack.combo_index])
            self.frame = frames[phase]
        elif player.dash_remaining > 1e-9:
            self.frame = 9
        elif not player.grounded:
            self.frame = 6 if player.vy > 100 else 7 if player.vy > -90 else 8
        elif abs(player.x - previous_x) > 1e-7:
            self.walk_clock += dt
            self.frame = 2 + int(self.walk_clock * 12) % 4
        else:
            self.walk_clock = 0.0
            self.frame = int(self.clock * 3) % 2
