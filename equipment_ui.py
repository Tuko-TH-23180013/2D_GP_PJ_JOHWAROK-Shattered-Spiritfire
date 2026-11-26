"""데모 장비창. 표시와 클릭 판정은 동일한 버튼 좌표를 공유한다."""
from equipment import ITEMS
import growth_settings as cfg


def buttons(game):
    gear = game.gear
    result = [('close', (1000, 590, 1090, 630), '닫기', 'Close')]
    for i, item in enumerate(gear.equipment.slots):
        label = ITEMS[item].name if item else '빈 칸'
        result.append((f'slot:{i}', (190, 465-i*65, 660, 520-i*65),
                       label, item or 'Empty'))
    for i, form in enumerate(gear.unlocked_forms):
        result.append((f'form:{form}', (710+i*180, 370, 875+i*180, 420),
                       '기본 폼' if form == 'basic' else '거대 방망이 폼', form))
    return result


def handle_clicks(game):
    # 닫기 클릭 뒤 나머지 입력이 월드/다른 버튼으로 새지 않는다.
    for x, y in game.inputs.clicks:
        for action, (left, bottom, right, top), _, _ in buttons(game):
            if left <= x <= right and bottom <= y <= top:
                if action == 'close':
                    game.gear.toggle()
                    return
                if action.startswith('slot:'):
                    game.gear.replace(int(action.split(':')[1]), game.player)
                elif action.startswith('form:'):
                    game.gear.select_form(game, action.split(':')[1])
                break


def draw(hud, game):
    from pico2d import pico2d as p2d
    gear, player = game.gear, game.player
    for drop in gear.drops:
        if drop.consumed:
            continue
        p2d.draw_rectangle(*game.camera.screen_rect(drop.x, drop.y, drop.x+24, drop.y+24),
                           235, 190, 105, filled=True)
    target = gear.nearest(player)
    if target and not gear.open:
        x, y = game.camera.screen_point(target.x+12, target.y+65)
        x = max(200, min(1080, x))
        hud.text(x, y, ITEMS[target.item_id].name, target.item_id, centered=True, font=hud.small)
        duplicate = target.item_id in gear.equipment.slots
        hud.text(x, y-20, 'F 획득 · 길게 1초: 골드 전환' if duplicate else 'F 획득 / 교체',
                 'F take / hold 1s convert' if duplicate else 'F take / replace',
                 centered=True, font=hud.small)
        if gear.hold_target is target:
            p2d.draw_rectangle(x-50, y-35, x-50+100*min(1, gear.hold_time/cfg.HOLD_SECONDS),
                               y-30, 240, 200, 100, filled=True)
    if not gear.open:
        return
    p2d.draw_rectangle(160, 165, 1120, 650, 18, 22, 36, filled=True)
    p2d.draw_rectangle(160, 165, 1120, 650, 180, 150, 100)
    hud.text(190, 610, '장비 · 게임 일시정지', 'Equipment / PAUSED', font=hud.title)
    hud.text(190, 555, '슬롯 클릭: 대기 아이템 교체 / 없으면 장비 해제',
             'Click slot: replace pending item / unequip', font=hud.small)
    for action, rect, ko, en in buttons(game):
        left, bottom, right, top = rect
        locked = action.startswith('form:') and not gear.can_change_form(game)
        p2d.draw_rectangle(*rect, *(70, 75, 85) if locked else (170, 150, 110))
        hud.text(left+10, (bottom+top)/2+5, ko, en, font=hud.small)
        if action.startswith('slot:'):
            item = gear.equipment.slots[int(action.split(':')[1])]
            if item:
                data = ITEMS[item]
                st = data.stats
                hud.text(left+10, bottom+10,
                         f'{data.inscription} · 공격 {st.attack:.0%} HP +{st.hp} 방어 {st.reduction:.0%} 파쇄 {st.stagger:.0%}',
                         f'ATK {st.attack:.0%} HP +{st.hp} DR {st.reduction:.0%} STG {st.stagger:.0%}', font=hud.small)
    hud.text(710, 520, f'HP {player.hp}/{player.max_hp}', font=hud.small)
    hud.text(710, 493, f'공격 ×{player.damage_multiplier:.2f} / 스태거 ×{player.stagger_multiplier:.2f}',
             f'ATK x{player.damage_multiplier:.2f} / STG x{player.stagger_multiplier:.2f}', font=hud.small)
    hud.text(710, 466, f'받는 피해 감소 {player.damage_reduction:.0%}',
             f'Damage reduction {player.damage_reduction:.0%}', font=hud.small)
    hud.text(710, 345, '폼 변경 가능' if gear.can_change_form(game) else '폼 잠김: 현재/예정 전투 또는 행동 중',
             'Form selection ready' if gear.can_change_form(game) else 'Locked: combat / pending wave / action', font=hud.small)
    counts = gear.equipment.counts()
    hud.text(190, 225, '각인: ' + ' / '.join(f'{k} {counts[k]}/{cfg.INSCRIPTION_THRESHOLD}' for k in ('맹공','수호','파쇄')),
             'Inscriptions: ' + str(list(counts.values())), font=hud.small)
    if gear.pending:
        hud.text(710, 300, '교체 대기: '+ITEMS[gear.pending.item_id].name,
                 'Pending: '+gear.pending.item_id, font=hud.small)
        hud.text(710, 275, '취소: 닫기 (바닥 아이템 유지)', 'Cancel: close (item stays)', font=hud.small)
