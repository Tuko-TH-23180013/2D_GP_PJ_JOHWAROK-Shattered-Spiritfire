"""데모 몬스터 시트 메타데이터. 전투 시간과 아트 프레임을 분리한다."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'Sprite_sheet' / 'Monster'


def load_catalog():
    result = {}
    for group in ('normal', 'mid', 'main'):
        data = json.loads((ROOT / group / 'sprites.json').read_text(encoding='utf-8'))
        for sheet in data['sheets']:
            result[sheet['id']] = {**sheet, 'file': ROOT / group / sheet['path']}
    return result


CATALOG = load_catalog()


def duration(sheet_id):
    return sum(f['duration_ms'] for f in CATALOG[sheet_id]['frames']) / 1000


def timed_frame(sheet_id, elapsed):
    frames = CATALOG[sheet_id]['frames']
    for frame in frames:
        elapsed -= frame['duration_ms'] / 1000
        if elapsed < -1e-9:
            return frame['index']
    return frames[-1]['index']


def pose(monster):
    kind = monster.kind
    if monster.hp <= 0:
        sheet = kind + '_death'
        return sheet, timed_frame(sheet, monster.death_age)
    if kind == 'guardian' and monster.state in ('DOWN', 'WAKE'):
        return 'guardian_reactions', 2 if monster.state == 'DOWN' else 3
    if kind == 'hahoe' and monster.state in ('DOWN', 'WAKE'):
        return 'hahoe_reactions', 1 if monster.state == 'DOWN' else 2
    sheet = monster.sheet
    if getattr(monster, 'hitstun_remaining', 0) > 0:
        return sheet, next((f['index'] for f in CATALOG[sheet]['frames'] if f['phase'] == 'recovery'), 0)
    phase = monster.attack.phase if monster.attack else monster.state
    names = {'STARTUP': 'windup', 'ACTIVE': 'active', 'RECOVERY': 'recovery',
             'CHASE': 'move', 'APPROACH': 'move'}
    desired = names.get(phase, 'idle')
    frames = CATALOG[sheet]['frames']
    if desired == 'windup' and any(f['phase'] == 'windup_hold' for f in frames):
        if monster.attack.elapsed >= monster.attack.data.startup / 3:
            desired = 'windup_hold'
    return sheet, next((f['index'] for f in frames if f['phase'] == desired), 0)
