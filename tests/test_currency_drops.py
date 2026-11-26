import unittest
from main import MapGame
from reward_system import REWARD_CURRENCY, REWARD_JADE


class CurrencyDropTests(unittest.TestCase):
    def test_all_tiers_burst_then_credit_exactly_once(self):
        for room,tier,count in ((0,'normal',2),(2,'mid',6),(6,'main',10)):
            game = MapGame()
            game.enter_room(room)
            actor = game.boss or game.enemies[0]
            actor.hp = 0
            actor.on_combat_hit()
            game.update(.01)
            self.assertEqual(len(game.rewards.currency_drops),count)
            self.assertEqual((game.rewards.gold,game.rewards.jade),(0,0))
            old = [(d.x,d.y) for d in game.rewards.currency_drops]
            game.update(.10)
            self.assertNotEqual(old,[(d.x,d.y) for d in game.rewards.currency_drops])
            for _ in range(180):
                game.update(1/60)
            self.assertEqual((game.rewards.gold,game.rewards.jade),
                             (REWARD_CURRENCY[tier],REWARD_JADE[tier]))
            self.assertFalse(game.rewards.currency_drops)

    def test_pause_chest_stops_drops(self):
        from reward_chest import RewardChest
        game = MapGame()
        game.enemies[0].hp = 0
        game.update(.01)
        before = [(d.x,d.y,d.age) for d in game.rewards.currency_drops]
        game.gear.chest_open = RewardChest('item',('fang',),100)
        game.update(10)
        self.assertEqual(before,[(d.x,d.y,d.age) for d in game.rewards.currency_drops])
        self.assertEqual(game.rewards.gold,0)

    def test_transition_settles_but_death_discards_pending(self):
        game = MapGame()
        game.rewards.jade = 10
        game.enemies[0].hp = 0
        game.update(.01)
        game.enter_room(1)
        self.assertEqual((game.rewards.gold,game.rewards.jade),(5,11))
        game.enemies[0].hp = 0
        game.update(.01)
        game.player.hp = 0
        game.update(.01)
        self.assertEqual((game.rewards.gold,game.rewards.jade),(0,11))
        self.assertFalse(game.rewards.currency_drops)

    def test_victory_continues_collection_without_world_combat(self):
        game = MapGame()
        game.enter_room(6)
        game.boss.hp = 0
        game.boss.on_combat_hit()
        for _ in range(120): game.update(1/60)
        self.assertTrue(game.victory)
        from reward_system import CurrencyDrop
        game.rewards.currency_drops.append(CurrencyDrop('gold',7,game.player.x+100,180,0,100))
        before = (game.elapsed,game.player.x,game.player.y)
        for _ in range(120): game.update(1/60)
        self.assertEqual(before,(game.elapsed,game.player.x,game.player.y))
        self.assertEqual((game.rewards.gold,game.rewards.jade),(157,30))
