import unittest
from boss import Boss
from player import Player
from world import World, Rect
from combat_system import CombatSystem
from attack import Attack, BASIC_COMBO


class BossTests(unittest.TestCase):
    def enter(self):
        from main import Game
        import sdl2
        game = Game()
        game.checkpoint.active = True
        game.player.x = 3100
        game.inputs.pressed = {sdl2.SDLK_UP}
        game.update(1 / 60)
        return game

    def test_gate_start_once_and_arena_barrier(self):
        game = self.enter()
        self.assertTrue(game.boss_active)
        boss = game.boss
        self.assertFalse(game.start_boss())
        self.assertIs(game.boss, boss)
        game.world.move_x(game.player, -1000)
        self.assertEqual(game.player.x, game.stage.arena_barrier.right)

    def test_boss_death_retry_resets_arena_and_boss(self):
        import sdl2
        game = self.enter()
        game.player.hp = 1
        game.player.x = game.boss.x - 80
        for _ in range(240):
            game.update(1 / 60)
            if game.player.hp == 0:
                break
        self.assertEqual(game.player.hp, 0)
        self.assertIsNone(game.boss.attack)
        game.inputs.pressed = {sdl2.SDLK_r}
        game.update(1 / 60)
        self.assertEqual(game.player.x, 2500)
        self.assertFalse(game.boss_active or game.victory)
        self.assertIsNone(game.boss)
        self.assertNotIn(game.stage.arena_barrier, game.world.solids)

    def test_real_damage_defeats_boss_and_freezes_victory(self):
        import sdl2
        game = self.enter()
        # 조작 숙련도 대신 공격→피해→다운/기상→승리 연결을 검증하는 무적 fixture.
        game.player.hurt_invulnerability = 100
        for frame in range(2400):
            game.player.x = game.boss.x - 70
            game.player.facing = 1
            game.inputs.pressed = {sdl2.SDLK_x} if frame % 12 == 0 else set()
            game.update(1 / 60)
            if game.victory:
                break
        self.assertTrue(game.victory)
        self.assertEqual(game.boss.hp, 0)
        self.assertIsNone(game.player.attack)
        x, elapsed = game.player.x, game.elapsed
        game.inputs.pressed = {sdl2.SDLK_x, sdl2.SDLK_SPACE}
        game.inputs.held = {sdl2.SDLK_RIGHT}
        game.update(0.05)
        self.assertEqual((game.player.x, game.elapsed), (x, elapsed))
        game.inputs.pressed = {sdl2.SDLK_r}
        game.update(0.05)
        self.assertFalse(game.victory)

    def test_giant_hit_has_same_result_across_frame_rates(self):
        import sdl2
        for fps in (20, 60, 144):
            game = self.enter()
            game.player.x = game.boss.x - 80
            game.player.weapon = 'giant'
            game.inputs.pressed = {sdl2.SDLK_x}
            game.update(1 / fps)
            game.inputs.pressed.clear()
            for _ in range(fps):
                game.update(1 / fps)
            self.assertEqual(game.boss.hp, 476)

    def test_down_wake_damage_and_repeat_recovery(self):
        boss, player, combat = Boss(400), Player(300), CombatSystem()
        world = World()
        for cycle in range(2):
            boss.cooldown = 0
            boss.update(0.01, player, world)
            for _ in range(8):
                attack = Attack(player, BASIC_COMBO[0])
                attack.advance(0.1)
                combat.begin_frame()
                combat.resolve([attack], [boss])
            self.assertEqual(boss.state, 'DOWN')
            self.assertIsNone(boss.attack)
            hp = boss.hp
            attack = Attack(player, BASIC_COMBO[0])
            attack.advance(0.1)
            combat.begin_frame()
            combat.resolve([attack], [boss])
            self.assertEqual(boss.hp, hp - 10)
            self.assertEqual(boss.stagger, 120)
            combat.update_target(boss, 2.01)
            boss.update(0.01, player, world)
            self.assertEqual(boss.state, 'WAKE')
            attack = Attack(player, BASIC_COMBO[0])
            attack.advance(0.1)
            combat.begin_frame()
            combat.resolve([attack], [boss])
            self.assertEqual(boss.hp, hp - 20)
            self.assertEqual(boss.stagger, 0)
            boss.update(0.71, player, world)
            self.assertEqual(boss.state, 'NORMAL')

    def test_lethal_hit_while_down_clears_attack(self):
        boss, player = Boss(400), Player(300)
        boss.hp = 5
        boss.state = 'DOWN'
        boss.stagger_remaining = 1
        attack = Attack(player, BASIC_COMBO[0])
        attack.advance(0.1)
        CombatSystem().resolve([attack], [boss])
        self.assertEqual(boss.state, 'DEAD')
        self.assertEqual(boss.hp, 0)
        self.assertIsNone(boss.attack)

    def test_patterns_alternate_and_have_windup(self):
        boss, player = Boss(400), Player(300)
        world = World([Rect(0, 0, 1000, 100)])
        seen = []
        previous = None
        for _ in range(1000):
            boss.update(0.01, player, world)
            if boss.attack is not None and boss.attack is not previous:
                seen.append(boss.pattern)
                self.assertEqual(boss.attack.phase, 'STARTUP')
                self.assertGreaterEqual(boss.attack.data.startup, 0.6)
                previous = boss.attack
            if len(seen) == 3:
                break
        self.assertEqual(seen, ['SWING', 'RUSH', 'SWING'])

    def test_rush_moves_only_active_and_stops_at_wall(self):
        boss, player = Boss(400), Player(300)
        world = World([Rect(0, 0, 1000, 100), Rect(200, 100, 220, 300)])
        boss.pattern_index = 1
        boss.cooldown = 0
        boss.update(0.01, player, world)
        for _ in range(50):
            boss.update(0.01, player, world)
        self.assertEqual(boss.x, 400)
        for _ in range(100):
            boss.update(0.01, player, world)
        self.assertEqual(boss.x, 220)

    def test_normal_hit_does_not_cancel_pattern(self):
        boss, player = Boss(400), Player(300)
        boss.cooldown = 0
        boss.update(0.01, player, World())
        current = boss.attack
        attack = Attack(player, BASIC_COMBO[0])
        attack.advance(0.1)
        CombatSystem().resolve([attack], [boss])
        self.assertEqual(boss.hp, 490)
        self.assertIs(boss.attack, current)
