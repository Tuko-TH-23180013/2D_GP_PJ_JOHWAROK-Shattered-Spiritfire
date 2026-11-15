"""SDL 없는 HUD 데이터 변환과 리소스 목록."""
from pathlib import Path
from settings import DASH_RECHARGE

ROOT = Path(__file__).resolve().parent
ASSETS = {p.stem: p for p in ROOT.glob('*/*.png')}


def ratio(value, maximum):
    return max(0.0, min(1.0, value / maximum)) if maximum > 0 else 0.0


def dash_levels(player):
    charges = max(0, min(2, player.dash_charges))
    progress = 1 - ratio(player.recharge_remaining, DASH_RECHARGE)
    return tuple(1.0 if i < charges else progress if i == charges else 0.0 for i in range(2))


def boss_visible(game):
    return bool(game.boss_active and game.boss is not None and game.boss.hp > 0 and not game.victory)
