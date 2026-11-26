"""임시 상자와 마우스 보상 선택창. 아이콘은 기존 데모 리소스를 재사용한다."""
from equipment import ITEMS, BONUSES
from special_abilities import NAMES
import growth_settings as cfg


def cards(chest):
    count = len(chest.choices)
    return [(i, (360+i*290 if count > 1 else 505, 420,
                 630+i*290 if count > 1 else 775, 510)) for i in range(count)]


def inside(point, rect):
    x, y = point
    l, b, r, t = rect
    return l <= x <= r and b <= y <= t


CLOSE = (920, 555, 1020, 595)
CONFIRM = (525, 185, 755, 230)


def handle_clicks(game):
    chest = game.gear.chest_open
    for point in game.inputs.clicks:
        if inside(point, CLOSE):
            game.gear.chest_open = None
            game.gear.reset_hold()
            return
        if inside(point, CONFIRM):
            if chest.claim(game):
                return
        for index, rect in cards(chest):
            if inside(point, rect):
                chest.selected = index


def details(chest, index):
    key = chest.choices[index]
    if chest.kind == 'item':
        item = ITEMS[key]
        s, bonus = item.stats, BONUSES[item.inscription]
        return [
            (item.name, key),
            (f'자체 효과: 공격 +{s.attack:.0%} / 최대 HP +{s.hp} / 피해 감소 {s.reduction:.0%} / 스태거 +{s.stagger:.0%}',
             f'ATK +{s.attack:.0%} / Max HP +{s.hp} / DR {s.reduction:.0%} / Stagger +{s.stagger:.0%}'),
            (f'각인 {item.inscription} · {cfg.INSCRIPTION_THRESHOLD}개: 공격 +{bonus.attack:.0%}, 피해 감소 {bonus.reduction:.0%}, 스태거 +{bonus.stagger:.0%}',
             f'Set {cfg.INSCRIPTION_THRESHOLD}: ATK +{bonus.attack:.0%} / DR {bonus.reduction:.0%} / Stagger +{bonus.stagger:.0%}'),
            ('중복은 바닥에서 F 획득/1초 전환 · 슬롯 초과는 교체창',
             'Duplicate: floor pickup/hold F convert. Full slots: replacement window.'),
        ]
    if key == 'enlarge':
        return [('거대화 · Shift', 'Enlarge / Shift'),
                (f'{cfg.GIANT_DURATION:g}초 지속 · 재사용 {cfg.GIANT_COOLDOWN:g}초 · 크기 {cfg.GIANT_SCALE:g}배',
                 f'Duration {cfg.GIANT_DURATION:g}s / Cooldown {cfg.GIANT_COOLDOWN:g}s / Size x{cfg.GIANT_SCALE:g}'),
                (f'피해 +{cfg.GIANT_DAMAGE:.0%}, 피해 감소 +{cfg.GIANT_REDUCTION:.0%} · 이동/대시 {cfg.GIANT_MOVE:.0%}/{cfg.GIANT_DASH:.0%}',
                 f'Damage +{cfg.GIANT_DAMAGE:.0%}, DR +{cfg.GIANT_REDUCTION:.0%}, move/dash {cfg.GIANT_MOVE:.0%}/{cfg.GIANT_DASH:.0%}'),
                ('공격·피격 범위 확대 / 지속 중 전투 가능', 'Larger attack/hurt boxes; combat allowed during buff')]
    return [('축지 · 방향키 + Shift', 'Blink / arrows + Shift'),
            (f'8방향 {cfg.BLINK_DISTANCE:g}px · 재사용 {cfg.BLINK_COOLDOWN:g}초',
             f'8 directions / {cfg.BLINK_DISTANCE:g}px / Cooldown {cfg.BLINK_COOLDOWN:g}s'),
            ('벽·천장·결계를 넘지 않음 / 무입력 시 바라보는 방향', 'Stops at walls/ceilings/barriers; no arrows: facing direction'),
            ('추가 무적 없음 · 공격/대시/폼 전환 중 발동 불가', 'No added invulnerability; blocked during attack/dash/form switch')]


def draw(hud, game):
    from pico2d import pico2d as p2d
    gear = game.gear
    if not gear.open:
        for chest in gear.chests:
            x, y = chest.x, chest.y
            color = (100, 90, 80) if chest.claimed else (115, 180, 245) if chest.kind == 'ability' else (225, 170, 70)
            for rect, tint in (((x-18,y,x+30,y+25), (55,40,32)),
                               ((x-18,y+25,x+30,y+(40 if chest.claimed else 34)),color),
                               ((x+3,y+10,x+10,y+28),color)):
                p2d.draw_rectangle(*game.camera.screen_rect(*rect), *tint, filled=True)
        nearby = gear.nearest_chest(game.player)
        if nearby and gear.chest_open is None:
            x,y = game.camera.screen_point(nearby.x+6,nearby.y+65)
            hud.text(max(130,min(1150,x)),y, 'F 능력 상자' if nearby.kind == 'ability' else 'F 아이템 상자',
                     'F ability chest' if nearby.kind == 'ability' else 'F item chest', centered=True, font=hud.small)
    chest = gear.chest_open
    if chest is None:
        return
    p2d.draw_rectangle(250,155,1040,620,18,22,36,filled=True)
    p2d.draw_rectangle(250,155,1040,620,185,155,100)
    hud.text(280,580,'보상 상자 · 게임 일시정지','Reward chest / PAUSED',font=hud.title)
    hud.text(280,540,'마우스를 올려 정보 확인 → 클릭 선택 → 획득','Hover for details / Click to select / Claim',font=hud.small)
    preview = chest.selected
    for i,rect in cards(chest):
        hover = inside(game.inputs.mouse,rect)
        if hover:
            preview = i
        p2d.draw_rectangle(*rect, *((110,230,235) if hover or chest.selected == i else (125,110,90)))
        x,y = (rect[0]+rect[2])/2,465
        key = chest.choices[i]
        if chest.kind == 'ability':
            hud.asset('skill_slash' if key == 'enlarge' else 'skill_spirit',x-80,y,42,42)
        else:
            hud.asset('slot_active',x-80,y,42,42)
        hud.text(x-45,y,NAMES[key] if chest.kind == 'ability' else ITEMS[key].name,key,font=hud.small)
    if preview is None and len(chest.choices) == 1:
        preview = 0
    if preview is not None:
        for i,(ko,en) in enumerate(details(chest,preview)):
            hud.text(285,385-i*35,ko,en,font=hud.small)
    for rect,ko,en in ((CLOSE,'닫기','Close'),(CONFIRM,'선택 보상 획득' if chest.selected is not None else '먼저 보상을 선택하세요',
                                             'Claim selected reward' if chest.selected is not None else 'Select a reward first')):
        p2d.draw_rectangle(*rect,180,150,100)
        hud.text((rect[0]+rect[2])/2,(rect[1]+rect[3])/2,ko,en,centered=True,font=hud.small)
