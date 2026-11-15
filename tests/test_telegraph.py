import unittest
from attack import Attack
from attack_telegraph import attack_telegraph
from monsters import Monster, SPECS
from demo_bosses import Hahoe, Guardian, SLASH, RUSH


class TelegraphTests(unittest.TestCase):
    def test_all_types_have_startup_warning_only(self):
        actors = [Monster(k, 500) for k in SPECS] + [Hahoe(500), Guardian(500)]
        for actor in actors:
            data = actor.spec.attack if isinstance(actor, Monster) else SLASH
            actor.attack = Attack(actor, data)
            actor.attack.elapsed = data.startup / 2
            cue = attack_telegraph(actor)
            self.assertAlmostEqual(cue.progress, .5)
            self.assertGreater(cue.bounds.right, cue.bounds.left)
            actor.attack.elapsed = data.startup
            self.assertIsNone(attack_telegraph(actor))
            actor.attack.elapsed = 0
            actor.hp = 0
            self.assertIsNone(attack_telegraph(actor))

    def test_locked_direction_and_dive_path(self):
        actor = Monster('sotdae', 500, 200)
        actor.dive_velocity = (-300, -200)
        actor.attack = Attack(actor, actor.spec.attack)
        cue = attack_telegraph(actor)
        self.assertLess(cue.end[0], cue.start[0])
        self.assertLess(cue.end[1], cue.start[1])
        actor.facing = 1
        self.assertEqual(cue, attack_telegraph(actor))

    def test_rush_warning_includes_travel(self):
        actor = Guardian(500)
        actor.pattern = 'RUSH'
        actor.attack = Attack(actor, RUSH)
        cue = attack_telegraph(actor)
        self.assertAlmostEqual(cue.start[0] - cue.end[0], 600 * RUSH.active)
        self.assertGreater(cue.bounds.right - cue.bounds.left, RUSH.reach)
