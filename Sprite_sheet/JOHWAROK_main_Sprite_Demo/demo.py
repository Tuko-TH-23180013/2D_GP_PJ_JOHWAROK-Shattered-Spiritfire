from dataclasses import dataclass
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT, FLOOR = 960, 540, 148
CELL, SCALE, ROWS = 160, 1.65, 5
STEP = 1 / 120

@dataclass(frozen=True)
class Strike:
    frames: tuple[int, int, int]
    timing: tuple[float, float, float]
    damage: int
    stagger: int
    reach: int
    effect: str

LIGHT = (
    Strike((10, 11, 12), (.09, .10, .18), 8, 14, 115, "forehand"),
    Strike((13, 14, 15), (.11, .11, .20), 10, 18, 125, "backhand"),
    Strike((16, 17, 18), (.19, .14, .29), 16, 28, 145, "slam"),
)
HEAVY = (
    Strike((22, 23, 24), (.24, .15, .29), 17, 25, 145, "slam"),
    Strike((16, 23, 18), (.31, .17, .36), 25, 40, 166, "heavy"),
)
AIR = (Strike((19, 20, 21), (.12, .13, .22), 10, 16, 110, "air"),)
HEAVY_AIR = (Strike((19, 20, 21), (.21, .16, .30), 18, 28, 132, "air"),)

class Demo:
    def __init__(self):
        self.x, self.y = 390., float(FLOOR)
        self.vy = 0.
        self.facing = 1
        self.weapon = self.attack_weapon = 0
        self.clock = self.walk_clock = 0.
        self.jumps = 0
        self.charges = 2
        self.refill = self.dash = self.dash_gap = 0.
        self.dash_dir = 1
        self.invulnerable = self.switch_fx = 0.
        self.queue = ()
        self.chain = 0
        self.age = 0.
        self.next_weapon = False
        self.combo_window, self.combo_step = 0., 0
        self.connected = False
        self.hp, self.stagger = 100, 0
        self.down = self.hit_flash = 0.
        self.dummy_x = 508
        self.hits = 0

    @property
    def strike(self):
        return self.queue[self.chain] if self.queue else None

    @property
    def phase(self):
        if not self.strike:
            return -1
        startup, active, _ = self.strike.timing
        if self.age < startup:
            return 0
        return 1 if self.age < startup + active else 2

    def start_attack(self):
        airborne = self.y > FLOOR or self.vy > 0
        self.attack_weapon = self.weapon
        if airborne:
            self.queue = HEAVY_AIR if self.weapon else AIR
        else:
            self.queue = HEAVY if self.weapon else LIGHT
        self.chain = self.combo_step if self.combo_window and not airborne else 0
        self.combo_window = 0.
        self.age = 0.
        self.connected = False
        self.dash = self.invulnerable = 0.

    def switch_weapon(self):
        self.weapon = 1 - self.weapon
        self.switch_fx = .24
        self.invulnerable = .085
        self.next_weapon = False
        self.combo_window, self.combo_step = 0., 0

    def finish_attack(self):
        self.combo_step = self.chain + 1
        self.combo_window = .38 if self.combo_step < len(self.queue) and self.attack_weapon == self.weapon else 0.
        self.queue = ()
        if self.next_weapon:
            self.switch_weapon()

    def start_dash(self):
        if self.charges == 0 or self.dash_gap > 0 or self.dash > 0:
            return False
        if self.charges == 2:
            self.refill = .72
        self.charges -= 1
        self.dash, self.dash_gap = .16, .23
        self.dash_dir = self.facing
        self.invulnerable = .065
        if self.phase == 2:
            self.finish_attack()
        return True

    def step(self, dt, direction=0, keys=()):
        self.clock += dt
        for timer in ("dash", "dash_gap", "invulnerable", "switch_fx", "hit_flash", "down", "combo_window"):
            setattr(self, timer, max(0., getattr(self, timer) - dt))
        if self.charges < 2:
            self.refill -= dt
            if self.refill <= 0:
                self.charges += 1
                self.refill += .72
        if direction and not self.strike and not self.dash:
            self.facing = direction
        if "c" in keys and self.jumps < 2:
            self.vy = 410 if self.jumps == 0 else 385
            self.jumps += 1
            self.invulnerable = 0.
        if "space" in keys:
            if self.strike and not self.dash:
                self.next_weapon = True
            else:
                self.switch_weapon()
        if "z" in keys:
            self.start_dash()
        if "x" in keys and "z" not in keys and not self.strike:
            self.start_attack()

        if self.strike:
            self.age += dt
            if self.phase == 1 and not self.connected:
                distance = (self.dummy_x - self.x) * self.facing
                if -10 <= distance <= self.strike.reach and self.y - FLOOR <= 112:
                    self.connected = True
                    self.hits += 1
                    self.hit_flash = .14
                    self.hp = max(0, self.hp - self.strike.damage)
                    if self.down == 0:
                        self.stagger += self.strike.stagger
                        if self.stagger >= 65:
                            self.down = .9
                            self.stagger = 0
            if self.age >= sum(self.strike.timing):
                self.finish_attack()

        if self.dash:
            self.x += self.dash_dir * 690 * dt
        elif not self.strike and direction:
            self.x += direction * 230 * dt
            self.walk_clock += dt
        elif self.strike and self.phase == 1 and self.queue in (LIGHT, HEAVY):
            self.x += self.facing * (85 if self.chain < 2 else 120) * dt
        self.x = min(WIDTH - 50, max(50, self.x))
        if self.y > FLOOR or self.vy > 0:
            self.y += self.vy * dt
            self.vy -= 1250 * dt
            if self.y <= FLOOR:
                self.y, self.vy, self.jumps = float(FLOOR), 0., 0

    def frame(self, direction):
        if self.strike:
            return self.strike.frames[self.phase]
        if self.dash:
            return 9
        if self.y > FLOOR:
            return 6 if self.vy > 100 else (7 if self.vy > -90 else 8)
        if direction:
            return (2, 3, 4, 5)[int(self.walk_clock * 12) % 4]
        return int(self.clock * 3) % 2

    def caption(self):
        if self.strike:
            title = "Air attack" if self.queue in (AIR, HEAVY_AIR) else f"{'Heavy' if self.attack_weapon else 'Basic'} {self.chain + 1}/{len(self.queue)}"
            return f"{title}  /  {('STARTUP', 'ACTIVE', 'RECOVERY')[self.phase]}"
        if self.dash:
            return "Dash"
        if self.switch_fx:
            return "Weapon switch"
        return "Heavy club" if self.weapon else "Basic club"

def autoplay(t):
    # All times are integer ticks. The GIF and the Pico2D loop share these inputs.
    sequence = {62:"x", 108:"x", 160:"x", 252:"c", 274:"c", 328:"x",
                428:"x", 454:"z", 507:"space", 633:"x", 719:"x"}
    direction = 1 if 380 <= t < 395 else 0
    if 529 <= t < 614:
        direction = -1
    if 619 <= t < 624:
        direction = 1
    key = sequence.get(t)
    return direction, (key,) if key else ()

def effects(model):
    """Return colored line segments in world coordinates."""
    color = (107, 239, 219)
    if model.phase == 1:
        settings = {
            "forehand": (-.62, .86, 95, 55), "backhand": (-1., 1.25, 105, 57),
            "slam": (1.48, -1.15, 114, 93), "air": (.86, -1.12, 102, 68),
            "heavy": (1.55, -1.4, 130, 99),
        }
        a, b, radius, height = settings[model.strike.effect]
        fraction = (model.age - model.strike.timing[0]) / model.strike.timing[1]
        end = min(1., max(.18, fraction + .24))
        start = max(0., end - .48)
        points = []
        for i in range(13):
            angle = a + (b-a) * (start+(end-start)*i/12)
            points.append((model.x+model.facing*(math.cos(angle)*radius),
                           model.y+height+math.sin(angle)*radius*.66))
        for p, q in zip(points, points[1:]):
            yield (*p, *q, color, 3)
    if model.switch_fx:
        for i in range(8):
            angle = i * math.tau / 8 + model.clock * 8
            radius = 39 + 45 * (.24-model.switch_fx)/.24
            x = model.x + math.cos(angle)*radius
            y = model.y + 52 + math.sin(angle)*radius*.8
            yield (x, y, x+4, y+8, color, 3)
    if model.dash:
        for i in range(6):
            x = model.x-model.facing*(30+10*i)
            y = model.y+24+i*6
            yield (x, y, x-model.facing*(20+i*4), y, (69, 130, 156), 2)

def run():
    import argparse
    import time
    import pico2d as p

    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="loop the animation showcase")
    parser.add_argument("--smoke", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    p.open_canvas(WIDTH, HEIGHT)
    try:
        scene = p.load_image(str(ROOT / "assets" / "village.png"))
        atlas = p.load_image(str(ROOT / "assets" / "hero.png"))
        dummy = p.load_image(str(ROOT / "assets" / "dummy.png"))
        font = p.load_font(str(ROOT / "assets" / "font.ttf"), 19)
        # Simple filled shapes use the same 1x1 sprite with a tint baked into it.
        colors = [(107,239,219), (69,130,156), (235,95,112), (27,42,59), (251,202,136)]
        swatches = {color: p.load_image(str(ROOT/"assets"/f"color{i}.png")) for i,color in enumerate(colors)}
        model, tick, direction = Demo(), 0, 0
        held, pending = set(), set()
        arrows = {p.SDLK_LEFT: -1, p.SDLK_RIGHT: 1}
        controls = {p.SDLK_c:"c", p.SDLK_x:"x", p.SDLK_z:"z", p.SDLK_SPACE:"space"}
        last, accum, rendered = time.perf_counter(), 0., 0
        while True:
            for event in p.get_events():
                if event.type == p.SDL_QUIT or (event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE):
                    return
                if event.type == p.SDL_KEYUP:
                    held.discard(event.key)
                if event.type != p.SDL_KEYDOWN or event.key in held:
                    continue
                held.add(event.key)
                if event.key == p.SDLK_r:
                    model, tick = Demo(), 0
                if event.key == p.SDLK_F1:
                    args.auto = not args.auto
                    model, tick = Demo(), 0
                if event.key in controls:
                    pending.add(controls[event.key])
            now = time.perf_counter()
            accum += min(.10, now-last)
            last = now
            while accum >= STEP:
                if args.auto:
                    if tick >= 840:
                        model, tick = Demo(), 0
                    direction, keys = autoplay(tick)
                else:
                    direction = sum(value for key, value in arrows.items() if key in held)
                    keys = pending
                model.step(STEP, direction, keys)
                tick += 1
                pending.clear()
                accum -= STEP

            p.clear_canvas()
            scene.draw(WIDTH/2, HEIGHT/2)
            dummy.draw(model.dummy_x, FLOOR+42-(15 if model.down else 0))
            swatches[colors[3]].draw(model.dummy_x, FLOOR+104, 84, 6)
            if model.hp:
                swatches[colors[2]].draw(model.dummy_x-42+.42*model.hp, FLOOR+104, .84*model.hp, 6)
            if model.stagger:
                swatches[colors[0]].draw(model.dummy_x-42+42*model.stagger/65, FLOOR+96, 84*model.stagger/65, 3)
            frame = model.frame(direction)
            sx, sy = frame % 5 * CELL, (ROWS-1-frame//5) * CELL
            # Cell foot pivot is (80, 133) measured from the PNG top left.
            cx, cy = model.x, model.y + (133-CELL/2)*SCALE
            atlas.clip_composite_draw(sx, sy, CELL, CELL, 0, 'h' if model.facing < 0 else '',
                                      cx, cy, CELL*SCALE, CELL*SCALE)
            for x, y, xx, yy, color, size in effects(model):
                swatches[color].composite_draw(math.atan2(yy-y,xx-x), '',
                    (x+xx)/2, (y+yy)/2, max(1, math.hypot(xx-x,yy-y)), size)
            if model.hit_flash:
                swatches[colors[4]].draw(model.dummy_x-20, FLOOR+53, 14, 3)
                swatches[colors[4]].draw(model.dummy_x-20, FLOOR+53, 3, 14)
            font.draw(44, 425, model.caption(), (173, 239, 226))
            font.draw(44, 390, f"Dash {model.charges}/2   Hits {model.hits}   Dummy HP {model.hp}", (191, 199, 213))
            p.update_canvas()
            rendered += 1
            if args.smoke and rendered >= 125:
                return
            p.delay(.008)
    finally:
        p.close_canvas()

if __name__ == "__main__":
    run()
