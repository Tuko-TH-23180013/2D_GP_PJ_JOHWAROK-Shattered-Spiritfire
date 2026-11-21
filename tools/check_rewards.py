"""실제 SDL 렌더링과 처치 보상/구슬 획득 연결 검사."""
from pathlib import Path
import sys
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pico2d import pico2d as p2d
from main import MapGame
from tools.check_monster_maps import capture


def main():
    p2d.open_canvas(1280, 720, sync=True)
    game = MapGame()
    present = p2d.update_canvas
    try:
        p2d.update_canvas = lambda: None
        game.rewards.rng = Mock(random=Mock(return_value=0))
        game.player.hp = 30
        for enemy in game.enemies:
            enemy.hp = 0
            enemy.on_combat_hit()
        for _ in range(120):
            game.update(1 / 60)
        assert game.rewards.balance == 10 and len(game.rewards.orbs) == 2
        game.draw()
        capture('johwarok-rewards-orbs.png')
        present()
        orb = game.rewards.orbs[0]
        game.player.x, game.player.y = orb.x, orb.y
        game.update(.02)
        assert game.player.hp == 50 and len(game.rewards.orbs) == 1
        for room, hp, money in ((2, 70, 60), (6, 100, 210)):
            game.enter_room(room, hp=30)
            game.boss.hp = 0
            game.boss.on_combat_hit()
            for _ in range(120):
                game.update(1 / 60)
            assert game.player.hp == hp and game.rewards.balance == money
            game.draw()
            capture(f'johwarok-rewards-boss-{room}.png')
            present()
            p2d.get_events()
        print('PASS: orb render/pickup, currency HUD, boss healing and victory')
    finally:
        p2d.update_canvas = present
        game.visuals = None
        p2d.close_canvas()


if __name__ == '__main__':
    main()
