# 조화록 · 장승마을 메인 보스 스프라이트

`sprite_viewer.html`을 열면 이 ZIP에 들어 있는 공격·반응·사망 모션을 볼 수 있습니다.
`sprites.json`의 경로는 압축을 푼 최상위 폴더 기준입니다.

| 몬스터 | 동작 | 파일 |
|---|---|---|
| 타락한 도깨비 수호신 | 직선 돌진 | `guardian/sprites/guardian.png` |
| 타락한 도깨비 수호신 | 피격 · 다운 · 기상 · 패배 | `guardian/sprites/guardian_reactions.png` |
| 타락한 도깨비 수호신 | 느린 대형 횡타 | `guardian/expansions/guardian_sweep.png` |
| 타락한 도깨비 수호신 | 무너진 몸체와 큰 혼불 | `guardian/deaths/guardian_death.png` |

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

- [타락한 도깨비 수호신](guardian/IMPLEMENTATION.md)
