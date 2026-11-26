"""실제 맵/물리로 정상·거대화 필수 지상 경로와 선택 발판 이동을 비교한다."""
import unittest
from map_route import ROOMS
from player import Player
from world import World, Rect
from settings import MOVE_SPEED, DASH_SPEED, DASH_DURATION
from tests.test_special_abilities import grant
import growth_settings as cfg


class GiantRouteTests(unittest.TestCase):
    def test_all_rooms_ground_route_without_waiting_for_expiry(self):
        for room in ROOMS:
            for giant in (False, True):
                p, world = Player(100, 100), room.create_world()
                if giant:
                    grant(p)
                    p.abilities.use(p, world)
                    p.abilities.giant_remaining = 100  # 경로 전체를 확대 상태로 검사
                for _ in range(1100):
                    p.update(1/60, 1, False, world)
                    if p.x + p.width >= room.boss_entrance.left:
                        break
                self.assertGreaterEqual(p.x+p.width, room.boss_entrance.left, room.name)
                self.assertEqual(p.y, 100)

    def test_traversal_platform_pair_actual_double_jump_at_multiple_fps(self):
        for room in ROOMS:
            if room.category != 'normal':
                continue
            first, second = [p for p in room.platforms if 1400 <= p.left < 1800]
            for fps in (20, 60, 144):
                for giant in (False, True):
                    world = room.create_world()
                    p = Player(first.right-55, first.top)
                    if giant:
                        grant(p)
                        p.abilities.use(p, world)
                    jumped_again = landed = False
                    destination = second.left+30
                    for tick in range(fps*2):
                        second_jump = not jumped_again and tick/fps >= .20
                        jumped_again |= second_jump
                        direction = 1 if p.x < destination else 0
                        p.update(1/fps, direction, tick == 0 or second_jump, world)
                        if p.grounded and abs(p.y-second.top) < 1e-6:
                            landed = True
                            break
                    self.assertTrue(landed, (room.name, fps, giant, p.x, p.y))
                    p.update(1/fps, 0, True, world, down_held=True)
                    for _ in range(fps): p.update(1/fps, 0, False, world)
                    self.assertAlmostEqual(p.y, 100)

    def test_dash_distance_and_gap_with_reduced_speed(self):
        for fps in (20, 60, 144):
            p = Player(100, 200)
            world = World([Rect(0, 0, 160, 100), Rect(250, 0, 500, 100)])
            grant(p)
            p.abilities.use(p, world)
            p.start_dash()
            remaining = DASH_DURATION
            while remaining > 1e-9:
                dt = min(remaining, 1/fps)
                p.update(dt, 0, False, world)
                remaining -= dt
            self.assertAlmostEqual(p.x, 100+DASH_SPEED*DASH_DURATION*cfg.GIANT_DASH)
            self.assertEqual(p.y, 200)
            for _ in range(fps): p.update(1/fps, 1, False, world)
            self.assertEqual(p.y, 100)

    def test_narrow_ceiling_activation_expiry_keeps_feet_and_terrain_body(self):
        world = World([Rect(0, 0, 500, 100), Rect(0, 170, 500, 190)])
        p = Player(100, 100)
        grant(p)
        before = (p.x, p.y, p.width, p.height)
        p.abilities.use(p, world)
        self.assertEqual(before, (p.x, p.y, p.width, p.height))
        p.update(.1, 1, False, world)
        self.assertEqual(p.y, 100)
        self.assertAlmostEqual(p.x, 100+MOVE_SPEED*cfg.GIANT_MOVE*.1)
        p.abilities.giant_remaining = .005
        p.update(.01, 0, False, world)
        self.assertEqual(p.y, 100)
        self.assertEqual(p.body_scale, 1)

    def test_blink_and_giant_dash_cannot_cross_encounter_gate(self):
        from main import MapGame
        game = MapGame()
        gate = game.encounters.gate
        game.player.x = gate.left-50
        grant(game.player, 'blink')
        game.abilities.use(game.player, game.world)
        self.assertEqual(game.player.x+game.player.width, gate.left)
        grant(game.player)
        game.abilities.use(game.player, game.world)
        game.player.update(.2, 1, False, game.world, dash_pressed=True)
        self.assertEqual(game.player.x+game.player.width, gate.left)

    def test_airborne_activation_and_expiry_do_not_teleport_feet(self):
        world = ROOMS[0].create_world()
        p = Player(1500, 220)
        p.update(.1, 0, True, world)
        before = (p.x, p.y, p.vy)
        grant(p)
        p.abilities.use(p, world)
        self.assertEqual(before, (p.x, p.y, p.vy))
        p.abilities.giant_remaining = .005
        control = Player(p.x, p.y)
        control.vy, control.jumps_used = p.vy, p.jumps_used
        p.update(.02, 0, False, world)
        control.update(.02, 0, False, world)
        self.assertAlmostEqual(p.y, control.y)
        self.assertAlmostEqual(p.vy, control.vy)
        self.assertEqual(p.body_scale, 1)
