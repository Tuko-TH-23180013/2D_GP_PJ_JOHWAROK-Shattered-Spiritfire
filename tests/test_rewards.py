import unittest

from main import MapGame


class CurrencyTests(unittest.TestCase):
    def test_defeat_once_and_tiers(self):
        game = MapGame()
        expected = 0
        for room, amount in ((0, 5), (2, 50), (6, 150)):
            game.enter_room(room)
            actor = game.boss or game.enemies[0]
            game.update(.01)
            self.assertEqual(game.rewards.balance, expected)
            actor.hp = 0
            actor.on_combat_hit()
            for _ in range(120):
                game.update(1 / 60)
            expected += amount
            self.assertEqual(game.rewards.balance, expected)

    def test_session_wallet_survives_player_replacement(self):
        game = MapGame()
        game.enemies[0].hp = 0
        game.update(.01)
        game.enter_room(3)
        game.saved_room = 3
        game.restart()
        self.assertEqual(game.rewards.balance, 5)
        self.assertEqual(MapGame().rewards.balance, 0)
