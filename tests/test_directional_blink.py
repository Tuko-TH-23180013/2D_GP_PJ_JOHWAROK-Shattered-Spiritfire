import math
import unittest
import sdl2
from main import MapGame, InputState
from player import Player
from world import World, Rect
from tests.test_special_abilities import grant
from growth_settings import BLINK_DISTANCE


class DirectionalBlinkTests(unittest.TestCase):
    def test_eight_directions_equal_distance_and_facing_fallback(self):
        for direction in ((1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)):
            p, world = Player(500,500), World([])
            grant(p, 'blink')
            self.assertTrue(p.abilities.use(p, world, direction))
            dx, dy = p.x-500, p.y-500
            self.assertAlmostEqual(math.hypot(dx,dy), BLINK_DISTANCE)
            self.assertAlmostEqual(dx, direction[0]*BLINK_DISTANCE/math.hypot(*direction))
            self.assertAlmostEqual(dy, direction[1]*BLINK_DISTANCE/math.hypot(*direction))
        p = Player(500,500)
        p.facing = -1
        grant(p, 'blink')
        p.abilities.use(p, World([]))
        self.assertEqual(p.x, 500-BLINK_DISTANCE)

    def test_diagonal_thin_obstacle_stops_on_straight_path(self):
        p = Player(100,100)
        world = World([Rect(220,200,221,500)])
        grant(p, 'blink')
        p.abilities.use(p, world, (1,1))
        self.assertAlmostEqual(p.x+p.width, 220)
        self.assertAlmostEqual(p.y-100, p.x-100)

    def test_ceiling_floor_and_contact_tangent(self):
        world = World([Rect(0,0,500,100), Rect(0,300,500,320), Rect(250,100,260,300)])
        p = Player(100,100)
        grant(p, 'blink')
        p.vy = 400
        self.assertTrue(p.abilities.use(p, world, (0,1)))
        self.assertEqual(p.y+p.height, 300)
        self.assertEqual(p.vy, 0)
        p.abilities.cooldowns['blink'] = 0
        self.assertFalse(p.abilities.use(p, world, (0,1)))
        self.assertEqual(p.abilities.cooldowns['blink'], 0)
        self.assertTrue(p.abilities.use(p, world, (0,-1)))
        self.assertEqual((p.y,p.grounded,p.jumps_used), (100,True,0))
        p.abilities.cooldowns['blink'] = 0
        self.assertTrue(p.abilities.use(p, world, (1,0)))
        self.assertEqual(p.x+p.width, 250)
        p.abilities.cooldowns['blink'] = 0
        self.assertTrue(p.abilities.use(p, world, (-1,0)))

    def test_one_way_pass_up_land_down_and_drop_ignored(self):
        platform = Rect(0,210,500,230,True)
        world = World([platform])
        p = Player(100,100)
        grant(p, 'blink')
        self.assertTrue(p.abilities.use(p, world, (0,1)))
        self.assertEqual(p.y,320)
        p.abilities.cooldowns['blink'] = 0
        self.assertTrue(p.abilities.use(p, world, (0,-1)))
        self.assertEqual(p.y,230)
        p.abilities.cooldowns['blink'] = 0
        self.assertFalse(p.abilities.use(p, world, (0,-1)))
        p.drop_platforms.add(platform)
        self.assertTrue(p.abilities.use(p, world, (0,-1)))
        self.assertEqual(p.y,10)

    def test_airborne_keeps_velocity_and_spent_jumps(self):
        p = Player(100,400)
        p.vy, p.jumps_used = -250, 2
        grant(p, 'blink')
        p.abilities.use(p, World([]), (1,1))
        self.assertEqual((p.vy,p.jumps_used,p.grounded), (-250,2,False))

    def test_boundary_and_barrier_in_actual_map(self):
        game = MapGame()
        p, gate = game.player, game.encounters.gate
        p.x, p.y = gate.left-60, 450
        grant(p,'blink')
        p.abilities.use(p,game.world,(1,1))
        self.assertLessEqual(p.x+p.width,gate.left+1e-7)
        p.abilities.cooldowns['blink'] = 0
        p.x, p.y = 20, 500
        p.abilities.use(p,game.world,(-1,1))
        self.assertAlmostEqual(p.x,0)
        self.assertLessEqual(p.y+p.height,720)

    def test_game_shift_and_hud_use_same_held_direction(self):
        for fps in (20,60,144):
            game = MapGame()
            grant(game.player, 'blink')
            game.player.x,game.player.y = 100,300
            game.inputs.held = {sdl2.SDLK_UP,sdl2.SDLK_LEFT}
            game.inputs.pressed = {sdl2.SDLK_LSHIFT}
            destination = game.abilities.blink_destination(game.player,game.world,game.inputs.ability_direction)
            self.assertTrue(game.abilities.available(game.player,game.world,game.inputs.ability_direction))
            game.update(1/fps)
            self.assertAlmostEqual(game.player.x,destination[0])  # left boundary holds normal motion too
            self.assertAlmostEqual(game.player.y,destination[1]-.5*1800/fps**2)
        inputs = InputState(held={sdl2.SDLK_UP,sdl2.SDLK_DOWN,sdl2.SDLK_LEFT,sdl2.SDLK_RIGHT})
        self.assertEqual(inputs.ability_direction,(0,0))
