import unittest
from unittest.mock import Mock

from main import MapGame
from reward_system import RewardSystem, VitalityOrb, heal
from player import Player
from world import World


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
        self.assertEqual(game.rewards.balance, 5)
        game.saved_room = 3
        game.restart()
        self.assertEqual(game.rewards.balance, 0)
        self.assertEqual(MapGame().rewards.balance, 0)


class HealingTests(unittest.TestCase):
    def test_drop_probability_boundary_and_once(self):
        for roll, count in ((0, 1), (.2499, 1), (.25, 0), (.99, 0)):
            game = MapGame()
            game.rewards = RewardSystem(Mock(random=Mock(return_value=roll)))
            game.enemies[0].hp = 0
            for _ in range(5):
                game.update(.01)
            self.assertEqual(len(game.rewards.orbs), count)
            game.rewards.rng.random.assert_called_once()

    def test_orb_falls_and_pickup_clamps_without_reviving(self):
        player, world = Player(100, 100), World()
        orb = VitalityOrb(100, 300)
        for _ in range(240):
            self.assertFalse(orb.update(1 / 240, world, player))
        self.assertEqual(orb.y, 100)
        player.hp = 0
        self.assertFalse(orb.update(.01, world, player))
        self.assertEqual(player.hp, 0)
        player.hp = 93
        self.assertTrue(orb.update(.01, world, player))
        self.assertEqual(player.hp, 100)

    def test_pickup_removed_and_room_transition_clears_drops(self):
        game = MapGame()
        game.player.hp = 30
        game.rewards.orbs = [VitalityOrb(100, 100)]
        game.update(.02)
        self.assertEqual(game.player.hp, 50)
        self.assertFalse(game.rewards.orbs)
        game.rewards.orbs = [VitalityOrb(600, 100)]
        game.enter_room(1, game.player.hp)
        self.assertFalse(game.rewards.orbs)
        self.assertEqual(game.player.hp, 50)

    def test_boss_heals_once_before_victory(self):
        for room, expected in ((2, 70), (6, 100)):
            game = MapGame()
            game.enter_room(room, hp=30)
            game.boss.hp = 0
            game.boss.on_combat_hit()
            game.update(.01)
            self.assertEqual(game.player.hp, expected)
            self.assertFalse(game.rewards.orbs)
            game.player.hp -= 5
            for _ in range(120):
                game.update(1 / 60)
            self.assertEqual(game.player.hp, expected - 5)
            self.assertEqual(game.victory, room == 6)

    def test_heal_preserves_combat_timers_and_does_not_revive(self):
        player = Player()
        player.hp = 99
        player.hurt_invulnerability = .3
        self.assertEqual(heal(player, 40), 1)
        self.assertEqual(player.hurt_invulnerability, .3)
        player.hp = 0
        self.assertEqual(heal(player, 100), 0)
