import unittest
from dataclasses import replace
from unittest.mock import patch
from camera import Camera
from player import Player
from map_route import ROOMS
from main import MapGame


class CameraZoomTests(unittest.TestCase):
    def test_world_coordinates_scale_around_ground_anchor(self):
        camera = Camera(1900, zoom=1.5, ground_screen_y=140)
        camera.x = 200
        self.assertEqual(camera.screen_point(200, 100), (0, 140))
        self.assertEqual(camera.screen_rect(210, 120, 250, 180), (15, 170, 75, 260))

    def test_follow_clamps_to_zoomed_world_edges(self):
        camera = Camera(1900, zoom=1.5)
        player = Player(900, 100)
        camera.follow(player)
        self.assertAlmostEqual(camera.screen_point(player.x + player.width / 2, 100)[0], 640)
        player.x = 1900 - player.width
        camera.follow(player)
        self.assertAlmostEqual(camera.screen_point(1900, 100)[0], 1280)
        player.x = 0
        camera.follow(player)
        self.assertEqual(camera.x, 0)

    def test_vertical_follow_keeps_high_jump_below_top_margin(self):
        camera = Camera(1900, zoom=1.5, ground_screen_y=140, vertical_follow=True)
        player = Player(900, 640)
        before = vars(player).copy()
        camera.follow(player)
        self.assertAlmostEqual(camera.screen_point(player.x, player.y + player.height)[1], 620)
        self.assertEqual(vars(player), before)
        player.y = 100
        camera.follow(player)
        self.assertEqual(camera.y, 0)

    def test_boss_room_can_override_zoom_without_changing_combat(self):
        rooms = list(ROOMS)
        rooms[6] = replace(rooms[6], camera_zoom=.75)
        with patch('map_route.ROOMS', tuple(rooms)):
            game = MapGame()
            self.assertEqual(game.camera.zoom, .9)
            game.enter_room(6)
            self.assertEqual(game.camera.zoom, .75)
            self.assertEqual(game.boss.hp, 500)
            self.assertEqual(game.player.width, 36)

    def test_invalid_zoom_rejected(self):
        with self.assertRaises(ValueError):
            Camera(1900, zoom=0)

    def test_zoomed_out_small_room_is_centered(self):
        camera = Camera(1280, zoom=.9)
        camera.follow(Player())
        left = camera.screen_point(0, 100)[0]
        right = camera.screen_point(1280, 100)[0]
        self.assertAlmostEqual(left, 1280 - right)
        self.assertGreater(left, 0)
