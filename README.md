# 조화록 — JOHWAROK: Shattered Spiritfire

Python/Pico2D 기반 1인 대학 게임 프로젝트입니다. 현재 0단계 실행 기반을 구현했습니다. 창, 테스트 사각형, 게임 루프, 입력, dt 제한과 종료 기능이 있으며 이동·전투·게임 에셋은 아직 없습니다.

## Windows 실행

확인 환경: Python **3.12.10**, Pico2D **1.5.1**, PySDL2 **0.9.17**, PySDL2-DLL **2.32.10**. 기존 PC에서 설치를 확인한 조합을 사용했습니다. 수업 지정 버전과의 일치 여부는 미확인입니다.

프로젝트 폴더에서 PowerShell로 실행합니다. 이미 `.venv`를 구성했다면 마지막 명령만 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

VS Code 인터프리터도 `.venv\Scripts\python.exe`로 선택합니다. 현재 PC에서는 `python`이 3.12.10으로 실행되지만 `py -0p`는 설치된 Python을 찾지 못하므로 `py` 런처에 의존하지 않습니다.

1280×720 창에 파란 테스트 사각형과 바닥선이 표시됩니다. 키를 누르고 있으면 사각형이 초록색으로 바뀝니다. 제목 표시줄에 FPS와 안내를 표시하며 **Esc** 또는 **창 닫기**로 종료합니다. 좌우 이동과 C 점프는 다음 단계입니다.

좌표는 왼쪽 아래 원점의 픽셀 단위이며 시간은 초 단위입니다. 긴 프레임의 dt는 최대 0.05초로 제한합니다. 창 크기·60 FPS 목표·dt 상한은 초기 개발용 임시 설정입니다.

## 확인

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe tools/check_bootstrap.py
```

실행 검사는 실제 창을 두 번 열어 각각 30프레임을 그린 뒤 Esc와 SDL 종료 이벤트를 주입합니다. 두 경로의 정상 종료를 확인했으며, 화면의 시각적 표시와 실제 키보드·닫기 버튼 조작은 직접 확인해야 합니다.

`.venv`, Python 캐시와 비밀정보 파일은 Git에서 제외합니다. 이미지·음원 의존성은 아직 없습니다.

## 문서 안내
- AGENTS.md: 개발 지침
- START_HERE.md: 처음 보낼 작업 요청
- docs/JOHWAROK_CODEX_HANDOFF.md: 업로드된 원본 그대로 보관
- docs/JOHWAROK_Incremental_Development.md: 원본에 포함된 개발 계획 분리본
- docs/STATUS.md: 현재 실제 상태와 다음 작업

이 묶음은 채팅 전체를 동기화하지 않습니다. 다른 채팅의 인계 자료를 추가할 때 최신 확정 내용과 충돌하는지 확인하고 문서를 갱신하세요.
