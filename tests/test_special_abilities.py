import unittest
import sdl2
from player import Player
from world import World, Rect
from main import MapGame
from attack import Attack, AttackData, BASIC_COMBO
from combat_system import CombatSystem
from training_dummy import TrainingDummy
import growth_settings as cfg


def grant(player, name='enlarge'):
    player.abilities.owned.add(name)
    player.abilities.equip(name)


class AbilityTests(unittest.TestCase):
    def test_enlarged_hurt_area_receives_hits_outside_terrain_body(self):
        p, enemy, world = Player(), TrainingDummy(), World()
        enemy.x, enemy.y, enemy.facing = 200, 100, -1
        data = AttackData('edge', .1, .1, .1, 10, 0, 35, 50)
        attack = Attack(enemy, data)
        attack.advance(.1)
        combat = CombatSystem()
        combat.resolve([attack], [p])
        self.assertEqual(p.hp, 100)
        grant(p)
        p.abilities.use(p, world)
        combat.resolve([attack], [p])
        self.assertEqual(p.hp, 92)

    def test_blink_rejects_platform_interior_without_cooldown(self):
        p = Player(100, 200)
        world = World([Rect(300, 210, 400, 230, True)])
        grant(p, 'blink')
        self.assertFalse(p.abilities.available(p, world))
        self.assertFalse(p.abilities.use(p, world))
        self.assertEqual((p.x, p.abilities.cooldowns['blink']), (100, 0))

    def test_giant_effects_and_expiry_restore_base(self):
        p, world = Player(), World()
        p.equipment.equip(0, 'fang')
        grant(p)
        self.assertTrue(p.abilities.use(p, world))
        self.assertAlmostEqual(p.damage_multiplier, 1.55)
        self.assertEqual(p.damage_reduction, .25)
        self.assertEqual(p.hurt_bounds.top-p.y, p.height*cfg.GIANT_SCALE)
        attack = Attack(p, BASIC_COMBO[0])
        self.assertEqual(attack.bounds.right-attack.bounds.left, 75*cfg.GIANT_SCALE)
        p.update(cfg.GIANT_DURATION, 0, False, world)
        self.assertEqual(p.body_scale, 1)
        self.assertAlmostEqual(p.damage_multiplier, 1.05)
        self.assertEqual(p.damage_reduction, 0)

    def test_shift_rejects_attack_dash_switch_without_cost(self):
        for state in ('attack', 'dash', 'switch'):
            p, world = Player(), World()
            grant(p)
            if state == 'attack': p.start_attack()
            elif state == 'dash': p.start_dash()
            else: p.perform_switch()
            self.assertFalse(p.abilities.use(p, world))
            self.assertEqual(p.abilities.cooldowns['enlarge'], 0)

    def test_giant_allows_actions_and_reduces_incoming_damage(self):
        p, world = Player(), World()
        grant(p)
        p.abilities.use(p, world)
        self.assertTrue(p.start_dash())
        p.update(.2, 1, False, world)
        self.assertAlmostEqual(p.x, 120 + 850*.2*cfg.GIANT_DASH)
        p.start_attack()
        self.assertIsNotNone(p.attack)
        p.update(.01, 0, True, world)
        self.assertGreater(p.vy, 0)
        enemy = TrainingDummy()
        enemy.x, enemy.y, enemy.facing = p.x-p.width, p.y, 1
        attack = Attack(enemy, BASIC_COMBO[0])
        attack.advance(.1)
        CombatSystem().resolve([attack], [p])
        self.assertEqual(p.hp, 92)  # 10 * .75 -> 8

    def test_independent_cooldowns_preserved_on_swap_and_map(self):
        game = MapGame()
        grant(game.player)
        game.abilities.use(game.player, game.world)
        grant(game.player, 'blink')
        self.assertTrue(game.abilities.use(game.player, game.world))
        self.assertEqual(game.abilities.cooldowns, {'enlarge': 15, 'blink': 5})
        game.enter_room(1)
        self.assertEqual(game.abilities.cooldowns, {'enlarge': 15, 'blink': 5})
        self.assertEqual(game.player.body_scale, cfg.GIANT_SCALE)
        game.restart()
        self.assertFalse(game.abilities.owned)
        self.assertEqual(sum(game.abilities.cooldowns.values()), 0)
        self.assertEqual(game.player.body_scale, 1)

    def test_blink_stops_at_wall_and_no_move_no_cost(self):
        p = Player(100, 100)
        world = World([Rect(0, 0, 500, 100), Rect(200, 100, 220, 720)])
        grant(p, 'blink')
        self.assertTrue(p.abilities.use(p, world))
        self.assertEqual(p.x, 200-p.width)
        p.abilities.cooldowns['blink'] = 0
        self.assertFalse(p.abilities.use(p, world))
        self.assertEqual(p.abilities.cooldowns['blink'], 0)
        self.assertFalse(p.invulnerable)

    def test_enlarged_combat_does_not_cross_barrier(self):
        p = Player(100, 100)
        target = TrainingDummy()
        target.x, target.y = 165, 100
        world = World([Rect(150, 0, 160, 720)])
        grant(p)
        p.abilities.use(p, world)
        attack = Attack(p, BASIC_COMBO[0])
        attack.advance(.1)
        hp = target.hp
        CombatSystem(world).resolve([attack], [target])
        self.assertEqual(target.hp, hp)

    def test_pause_retains_buff_cooldown_and_attack(self):
        game = MapGame()
        grant(game.player)
        game.abilities.use(game.player, game.world)
        game.player.start_attack()
        game.gear.open = True
        before = (game.abilities.giant_remaining, dict(game.abilities.cooldowns), game.player.attack.elapsed)
        game.update(100)
        self.assertEqual(before, (game.abilities.giant_remaining, game.abilities.cooldowns, game.player.attack.elapsed))
        game.inputs.pressed = {sdl2.SDLK_TAB}
        game.update(100)
        self.assertEqual(game.abilities.giant_remaining, before[0])
        game.inputs.pressed.clear()
        game.update(.01)
        self.assertAlmostEqual(game.abilities.giant_remaining, before[0]-.01)

    def test_first_reward_selects_only_one(self):
        from equipment_ui import handle_clicks
        game = MapGame()
        game.encounters.completed = 1
        game.gear.award(game)
        game.gear.open = True
        game.inputs.clicks = [(750, 200), (920, 200)]
        handle_clicks(game)
        self.assertEqual(game.abilities.owned, {'enlarge'})
        game.gear.award(game)
        self.assertFalse(game.gear.special_choices)
