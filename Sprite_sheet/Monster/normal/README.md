# 조화록 · 장승마을 일반 몬스터 스프라이트

`sprite_viewer.html`을 열면 이 ZIP에 들어 있는 공격·반응·사망 모션을 볼 수 있습니다.
`sprites.json`의 경로는 압축을 푼 최상위 폴더 기준입니다.

| 몬스터 | 동작 | 파일 |
|---|---|---|
| 깨진 장승귀 | 양팔 내려찍기 | `jangseung/sprites/jangseung.png` |
| 솟대새 원령 | 급강하 찌르기 | `sotdae/sprites/sotdae.png` |
| 잔불 도깨비 | 청염탄 1발 | `ember/sprites/ember.png` |
| 탈붙이 | 도약 할퀴기 | `mask/sprites/mask.png` |
| 장독귀 | 뚜껑 예고 후 박치기 | `onggi/sprites/onggi.png` |
| 뒤주귀 | 쌀알·청염 분출 | `rice_chest/sprites/rice_chest.png` |
| 지게귀 | 장작짐 돌진 | `jige/sprites/jige.png` |
| 깨진 장승귀 | 목재 파편과 흙먼지 | `jangseung/deaths/jangseung_death.png` |
| 솟대새 원령 | 부서진 날개와 혼불 | `sotdae/deaths/sotdae_death.png` |
| 잔불 도깨비 | 수축 후 혼불 소멸 | `ember/deaths/ember_death.png` |
| 탈붙이 | 떨어진 탈과 먹빛 먼지 | `mask/deaths/mask_death.png` |
| 장독귀 | 옹기 파편과 재 | `onggi/deaths/onggi_death.png` |
| 뒤주귀 | 쌀알과 나무 먼지 | `rice_chest/deaths/rice_chest_death.png` |
| 지게귀 | 장작과 흙먼지 | `jige/deaths/jige_death.png` |

## 스프라이트 관리 규칙

- 1지역은 메인 보스, 중간 보스, 일반 몬스터의 분류별 ZIP 세 개를 기준으로 관리합니다.
- 새 몬스터는 해당 분류의 ZIP 안에 몬스터 ID 폴더를 만듭니다. 기존 몬스터의 새 모션은 같은 폴더에 추가합니다.
- 경로는 `<몬스터 ID>/sprites/`(기본·공격·반응), `<몬스터 ID>/deaths/`(사망), `<몬스터 ID>/expansions/`(추가 패턴 후보)입니다.
- 새 시트를 넣으면 같은 ZIP의 `sprites.json`과 뷰어를 함께 갱신합니다. 작업마다 별도 ZIP을 만드는 대신 기존 분류 ZIP의 다음 버전으로 저장합니다.
- Pico2D에서 `frame_size`, `pico2d_pivot`, `frames`를 사용합니다. 사망은 1회 재생하고 마지막 투명 프레임에서 끝냅니다.

스프라이트와 뷰어는 아트 자료입니다. 게임 상태 및 히트박스 연동은 실제 프로젝트에서 진행합니다.


## VS Code에서 Codex로 구현하기

ZIP을 푼 뒤 몬스터 폴더와 루트의 `sprites.json`을 프로젝트에 추가한다. VS Code에서 Codex에 아래 구현 지침을 첨부한다. 일반 몬스터를 한 종씩 옮긴 경우에는 `sprites.json`에서 해당 `monster_id`의 항목만 로드한다.

> 이 구현 지침과 sprites.json을 읽고 기존 전투·충돌·씬 코드를 먼저 확인해. 기존 Attack과 CombatSystem이 있으면 재사용하고, 이 몬스터의 기본 동작부터 공격, 스태거, 사망까지 연결한 뒤 지침의 완료 확인을 실행해. 시연용 수치와 실제 코드의 값이 다르면 기존 설정을 우선하고 차이를 알려줘.

- [깨진 장승귀](jangseung/IMPLEMENTATION.md)
- [솟대새 원령](sotdae/IMPLEMENTATION.md)
- [잔불 도깨비](ember/IMPLEMENTATION.md)
- [탈붙이](mask/IMPLEMENTATION.md)
- [장독귀](onggi/IMPLEMENTATION.md)
- [뒤주귀](rice_chest/IMPLEMENTATION.md)
- [지게귀](jige/IMPLEMENTATION.md)
