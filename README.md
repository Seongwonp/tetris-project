# Tetris

Python + pygame으로 구현한 클래식 테트리스 게임입니다.

```
┌──────────────────────┬──────────┐
│                      │  NEXT    │
│  ##                  │  [블록]  │
│   ##                 ├──────────┤
│    ####              │  HOLD    │
│##########            │  [블록]  │
│                      ├──────────┤
│                      │ SCORE    │
│                      │  1,200   │
│                      │ LEVEL  2 │
│                      │ LINES 15 │
└──────────────────────┴──────────┘
```

## 실행 데모 (MP4)

https://github.com/user-attachments/assets/bb3dfbaf-eb32-40aa-82b3-1b24349b2810





## 기능

- 테트로미노 7종 (I, O, T, S, Z, J, L)
- 고스트 블록 (낙하 위치 미리 표시)
- 7-bag 랜덤 + NEXT 3개 미리보기
- HOLD / 고스트 블록
- DAS / ARR 입력 처리
- Lock delay
- T-Spin / Combo / Back-to-Back 점수
- 마라톤 / 스프린트 / 타임어택 모드
- 테마 / BGM 선택 / 키 리바인딩
- 하이스코어 / 통계 / 업적 / 리플레이 저장
- 하드 드롭 · 소프트 드롭
- Wall Kick 회전 보정
- 줄 제거 점수 (1줄=100, 2줄=300, 3줄=500, 4줄=800) × 레벨 배율
- 레벨 업 (10줄마다) → 낙하 속도 증가
- 점수 기준 스피드업 + "SPEED UP!" 표시
- 타이틀/모드/설정/스코어/리플레이/업적 화면
- 합성 효과음 (이동·회전·드롭·줄제거·게임오버)
- 뮤트 토글

## 프로젝트 구조

```
tetris-project/
├── main.py               # 진입점 – 이벤트 루프 & 입력 처리
├── requirements.txt
├── assets/               # 추후 이미지·음악 파일 추가 공간
├── tests/
└── tetris/
    ├── __init__.py
    ├── bag.py             # 7-bag 랜덤
    ├── config.py          # 입력/점수/속도 상수
    ├── modes.py           # Marathon / Sprint / Time Attack
    ├── profile.py         # 설정/하이스코어/통계 저장
    ├── replay.py          # 리플레이 기록 저장
    ├── piece.py          # 테트로미노 데이터 & 회전 로직
    ├── board.py          # 그리드 상태, 충돌 감지, 줄 제거
    ├── game.py           # 게임 상태 관리 (점수·레벨·홀드·낙하)
    ├── renderer.py       # pygame 렌더링 전담
    ├── themes.py         # UI 테마
    └── sound.py          # numpy 합성 효과음
```

## 설치 & 실행

```bash
# 1. 저장소 클론
git clone https://github.com/<your-id>/tetris-project.git
cd tetris-project

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 실행
python main.py
```

> Python 3.9 이상 권장

## 조작법

| 키 | 동작 |
|---|---|
| `←` / `→` | 좌우 이동 |
| `↑` | 시계 방향 회전 |
| `↓` | 소프트 드롭 (천천히 내리기) |
| `Space` | 하드 드롭 (즉시 바닥) |
| `C` | 홀드 |
| `P` | 일시정지 / 재개 |
| `R` | 재시작 |
| `M` | 효과음 뮤트 토글 |

게임 오버 화면에서는 아무 키로 재시작됩니다. (단, `M`은 뮤트 토글)

### 메뉴

| 화면 | 동작 |
|---|---|
| 타이틀 | `↑↓` 선택, `Enter` 실행 |
| 모드 선택 | `←→` 시작 레벨, `↑↓` 모드, `Enter` 확정 |
| 설정 | `←→` 값 변경, `Enter` 세부 설정 |
| 키 리바인딩 | `Enter` 후 원하는 키 입력 |
| 스코어/리플레이/업적 | 아무 키로 뒤로가기 |

## BGM

루트 경로에 있는 MP3/OGG를 자동으로 **랜덤 재생**합니다. 대상 파일은  
`03. A-Type Music (Korobeiniki).mp3`, `04. B-Type Music.mp3`, `05. C-Type Music.mp3`, `01. Title.mp3`, `bgm.ogg`, `bgm.mp3` 입니다.  
`M` 키로 뮤트하면 BGM도 함께 멈춥니다.

## 테스트 / 빌드

`python -m unittest discover -s tests` 로 핵심 규칙 테스트를 실행할 수 있습니다.  
테스트 범위는 7-bag/콤보/백투백/접지 제어 같은 규칙, 프로필 저장, BGM/테마 순환, 리플레이 요약, 모드 정의를 포함합니다.  
GitHub Actions에서 푸시/PR 시 테스트를 돌리고, 태그 릴리즈에서는 소스 ZIP를 자동으로 묶도록 설정해뒀습니다.

## 저장 위치

- 프로필/설정/하이스코어: `~/.tetris_project/profile.json`
- 리플레이: `~/.tetris_project/replays/`

## 점수 체계

| 줄 제거 | 기본 점수 | 비고 |
|---|---|---|
| 1줄 | 100 | |
| 2줄 | 300 | |
| 3줄 | 500 | |
| 4줄 (테트리스) | 800 | |
| 소프트 드롭 | +1/셀 | |
| 하드 드롭 | +2/셀 | |

최종 점수 = 기본 점수 × 현재 레벨

## 의존성

| 패키지 | 버전 | 용도 |
|---|---|---|
| [pygame](https://www.pygame.org/) | ≥ 2.0 | 렌더링, 입력, 사운드 |
| [numpy](https://numpy.org/) | ≥ 1.21 | 효과음 사인파 합성 |

## 아키텍처

```
main.py
  └─ GameState (game.py)   ← 게임 상태·규칙 (pygame 비의존)
       ├─ Board  (board.py) ← 그리드 & 충돌
       └─ Piece  (piece.py) ← 테트로미노

  └─ Renderer  (renderer.py) ← 화면 출력 (GameState 읽기 전용)
  └─ SoundManager (sound.py) ← 효과음 콜백
```

`GameState`는 pygame에 의존하지 않으므로 단독 테스트가 가능합니다.

## 참고 문헌

- **The Tetris Guideline** – Tetris Company 공식 게임 규칙 (회전, Wall Kick, 점수 체계 기준)  
  https://tetris.wiki/Tetris_Guideline
- **pygame 공식 문서** – pygame 2.x API 레퍼런스  
  https://www.pygame.org/docs/
- **numpy 공식 문서** – 배열 기반 사운드 합성에 활용  
  https://numpy.org/doc/stable/
- **Tetris Wiki – Scoring** – 점수 테이블 및 레벨 설계 참고  
  https://tetris.wiki/Scoring
- **Tetris Wiki – SRS (Super Rotation System)** – Wall Kick 오프셋 테이블  
  https://tetris.wiki/Super_Rotation_System

## AI 프롬프트 문서

이 프로젝트는 AI(Claude)의 도움으로 생성되었습니다.  
각 모듈별 생성 프롬프트와 유지보수용 추가 프롬프트는 아래 문서를 참고하세요.

- [docs/ai-prompts.md](docs/ai-prompts.md)

## 라이선스

MIT
