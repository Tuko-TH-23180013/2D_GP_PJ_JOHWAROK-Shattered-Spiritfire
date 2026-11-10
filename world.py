"""1단계 연습장과 축별 직사각형 충돌. 화면/SDL에 의존하지 않는다."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    left: float
    bottom: float
    right: float
    top: float


class World:
    def __init__(self, solids=None):
        self.solids = list(solids) if solids is not None else [
            Rect(0, 0, 1280, 100),
            Rect(-40, 0, 0, 720),
            Rect(1280, 0, 1320, 720),
            Rect(0, 720, 1280, 760),
            Rect(280, 210, 450, 235),
            Rect(530, 340, 710, 365),
            Rect(810, 470, 1010, 495),
            Rect(1070, 100, 1120, 270),
        ]

    def move_x(self, body, distance):
        target = body.x + distance
        for solid in self.solids:
            if body.y < solid.top and body.y + body.height > solid.bottom:
                if distance > 0 and body.x + body.width <= solid.left:
                    if target + body.width >= solid.left:
                        target = min(target, solid.left - body.width)
                elif distance < 0 and body.x >= solid.right:
                    if target <= solid.right:
                        target = max(target, solid.right)
        body.x = target

    def move_y(self, body, distance):
        target = body.y + distance
        landed = False
        hit = False
        for solid in self.solids:
            if body.x < solid.right and body.x + body.width > solid.left:
                if distance < 0 and body.y >= solid.top and target <= solid.top:
                    target = max(target, solid.top)
                    landed = hit = True
                elif (distance > 0 and body.y + body.height <= solid.bottom
                      and target + body.height >= solid.bottom):
                    target = min(target, solid.bottom - body.height)
                    hit = True
        body.y = target
        return landed, hit
