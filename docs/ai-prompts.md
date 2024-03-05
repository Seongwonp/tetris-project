# AI 프롬프트 문서

이 프로젝트는 Claude (Anthropic)와 함께 작성되었습니다.  
유지보수·기능 추가 시 아래 프롬프트를 참고하거나 그대로 붙여넣어 사용하세요.

---

## 목차

1. [프로젝트 초기 생성](#1-프로젝트-초기-생성)
2. [piece.py – 테트로미노](#2-piececpy--테트로미노)
3. [board.py – 게임 보드](#3-boardpy--게임-보드)
4. [game.py – 게임 상태](#4-gamepy--게임-상태)
5. [renderer.py – 렌더링](#5-rendererpy--렌더링)
6. [sound.py – 효과음](#6-soundpy--효과음)
7. [main.py – 진입점](#7-mainpy--진입점)
8. [유지보수용 추가 프롬프트](#8-유지보수용-추가-프롬프트)

---

## 1. 프로젝트 초기 생성

```
Python + pygame으로 테트리스 게임 프로젝트를 만들어줘.
단일 파일이 아니라 패키지 구조로:

tetris-project/
├── main.py
├── requirements.txt
├── assets/
└── tetris/
    ├── __init__.py
    ├── piece.py
    ├── board.py
    ├── game.py
    ├── renderer.py
    └── sound.py

각 모듈의 책임을 명확히 분리해줘:
- piece.py : 테트로미노 데이터 & 회전만
- board.py : 그리드 상태, 충돌 감지, 줄 제거만
- game.py  : 점수·레벨·홀드·낙하 타이밍 등 게임 상태 관리
             (pygame에 의존하지 않도록)
- renderer.py : pygame 화면 출력만 (GameState를 읽기 전용으로 사용)
- sound.py    : numpy로 사인파 합성해서 효과음 생성
```

---

## 2. `piece.py` – 테트로미노

```
tetris/piece.py를 작성해줘.

요구사항:
- 테트로미노 7종 (I, O, T, S, Z, J, L) 정의
- 각 종류에 색상(RGB 튜플)과 초기 shape(2D 리스트) 부여
- dataclass로 Piece 구현
- rotated_shape() 메서드: 시계 방향 90도 회전한 새 shape 반환
- clone() 메서드: 깊은 복사 반환
- 초기 x 위치는 보드 중앙에 자동 배치

board.py에 의존하지 말고, COLS 상수를 이 파일 안에 정의해줘.
```

---

## 3. `board.py` – 게임 보드

```
tetris/board.py를 작성해줘.

요구사항:
- ROWS=20, COLS=10 그리드 관리
- is_valid(piece, dx, dy, shape): 충돌 감지
  - 범위 밖 (left, right, bottom) 체크
  - 이미 고정된 블록과의 겹침 체크
  - shape 파라미터 옵션: 회전 미리보기에 사용
- lock(piece): piece를 그리드에 고정
- clear_lines(): 완성된 줄 제거 후 개수 반환
- ghost_y(piece): 하드드롭 시 착지 y 좌표 반환
- is_cell_filled(row, col): 셀의 kind 값 반환
```

---

## 4. `game.py` – 게임 상태

```
tetris/game.py를 작성해줘.

요구사항:
- pygame에 전혀 의존하지 않을 것 (단독 테스트 가능)
- GameState 클래스:
  - reset(): 게임 초기화
  - move(dx): 좌우 이동
  - rotate(): 시계 방향 회전 + Wall Kick (오프셋 0, -1, +1, -2, +2 순 시도)
  - soft_drop(): 한 칸 내리기, 착지 시 lock
  - hard_drop(): 즉시 바닥으로, 셀당 +2점
  - hold(): 홀드 교체, 한 턴에 한 번만 가능
  - toggle_pause(): 일시정지 토글
  - update(dt): 매 프레임 호출, 낙하 타이밍 처리
- 점수: {1줄:100, 2줄:300, 3줄:500, 4줄:800} × 레벨
- 레벨: 10줄마다 +1, 낙하 속도 max(50, 500-(level-1)*45) ms
- on_sound 콜백: "move", "rotate", "drop", "clear", "gameover" 이벤트 전달
```

---

## 5. `renderer.py` – 렌더링

```
tetris/renderer.py를 작성해줘.

요구사항:
- Renderer 클래스, draw(state: GameState) 한 메서드로 전체 화면 갱신
- 보드 영역 (COLS*CELL × ROWS*CELL):
  - 배경 그리드 라인
  - 고정 블록 (kind → COLORS[kind])
  - 고스트 블록 (낙하 위치, 반투명 외곽선)
  - 현재 블록
- 사이드바 (오른쪽, 폭 210):
  - NEXT / HOLD 미니 프리뷰 박스
  - HOLD는 can_hold=False일 때 어둡게 표시
  - SCORE / LEVEL / LINES 수치
  - 조작 안내 (← → ↑ ↓ SPACE C P R M)
- 오버레이: GAME OVER / PAUSED 반투명 패널
- 블록 셀: 둥근 모서리(border_radius=4), 하이라이트 테두리
```

---

## 6. `sound.py` – 효과음

```
tetris/sound.py를 작성해줘.

요구사항:
- numpy로 사인파(sin wave) 합성해서 pygame.mixer.Sound 생성
- SoundManager 클래스:
  - play(name): "move" | "rotate" | "drop" | "clear" | "gameover"
  - toggle(): 뮤트 온/오프, bool 반환
- 각 효과음 주파수·길이:
  - move:     300Hz, 40ms
  - rotate:   500Hz, 55ms
  - drop:     150Hz, 80ms
  - clear:    880Hz, 140ms
  - gameover: 100Hz, 400ms
- numpy 없으면 소리 없이 조용히 실패 처리 (게임은 정상 동작)
```

---

## 7. `main.py` – 진입점

```
tetris/main.py를 작성해줘.

요구사항:
- pygame 초기화, 화면 생성, FPS=60 고정
- pygame.key.set_repeat(160, 55)로 키 연속 입력 지원
- GameState, Renderer, SoundManager 연결
- 키 입력 처리:
  - R: 게임오버 여부 무관하게 리셋
  - P: 일시정지 토글
  - ← →: move(-1/+1)
  - ↑: rotate
  - ↓: soft_drop
  - SPACE: hard_drop
  - C: hold
  - M: sound.toggle()
- Python 3.9+ 호환 (match 문 사용하지 않기)
```

---

## 8. 유지보수용 추가 프롬프트

### 기능 추가

#### 배경음악 추가
```
tetris/sound.py의 SoundManager에 배경음악 기능을 추가해줘.
- assets/bgm.ogg 파일을 pygame.mixer.music으로 루프 재생
- play_bgm() / stop_bgm() 메서드 추가
- toggle()에서 뮤트 시 음악도 함께 정지
- 파일이 없으면 조용히 스킵
```

#### 하이스코어 저장
```
tetris/ 패키지에 highscore.py를 추가해줘.
- JSON 파일(~/.tetris_scores.json)에 상위 10개 기록 저장
- HighScoreManager 클래스:
  - load() → List[dict]  (name, score, lines, level, date)
  - save(name, score, lines, level)
  - is_high_score(score) → bool
- game.py의 GameState는 건드리지 말고,
  main.py에서 게임오버 시 호출하도록 해줘.
```

#### 다음 블록 3개 표시
```
tetris/game.py의 GameState를 수정해줘.
- next 단일 Piece 대신 next_queue: List[Piece] (3개) 관리
- 7-bag 랜덤 시스템 적용
  (7종을 한 세트로 섞어서 순서대로 꺼내는 방식)
- tetris/renderer.py의 사이드바 NEXT 영역도 3개 표시하도록 수정
```

#### 레벨 선택 시작 화면
```
main.py에 시작 화면을 추가해줘.
- 게임 시작 전 레벨(1~10) 선택 UI 표시
- ↑↓로 레벨 선택, ENTER로 시작
- 선택한 레벨을 GameState.reset(start_level=n)에 전달
- game.py의 reset()에 start_level 파라미터 추가
```

#### 저장 데이터와 리플레이
```
tetris/profile.py와 tetris/replay.py를 확장해줘.
- 프로필은 settings / stats / highscores / achievements를 JSON으로 저장
- highscores는 모드별로 정렬하고 최대 10개만 유지
- cycle_theme(), cycle_bgm_mode() 같은 설정 순환 메서드를 보강
- 리플레이는 이벤트 기록과 최근 리플레이 요약 목록을 제공
```

#### 테스트 확장
```
tests/ 디렉터리에 회귀 테스트를 더 추가해줘.
- profile 저장/로드와 partial data merge 검증
- highscores 정렬/trim, theme/bgm 순환 검증
- replay recent_summaries()가 invalid JSON을 건너뛰는지 검증
- mode 정의와 저장 데이터 기본값이 유지되는지 검증
```

---

### 버그 수정

#### 회전 관련 버그
```
tetris/game.py의 rotate()가 [증상 설명]하는 버그가 있어.
현재 Wall Kick 오프셋: [0, -1, 1, -2, 2]
SRS 규격의 정확한 오프셋 테이블로 교체해줘.
참고: https://tetris.wiki/Super_Rotation_System
```

#### 성능 최적화
```
tetris/renderer.py가 매 프레임 전체를 다시 그리고 있어.
변경된 셀만 dirty rect로 업데이트하도록 최적화해줘.
pygame.display.update(dirty_rects) 방식 사용.
```

---

### 테스트 작성

```
tests/ 디렉터리를 만들고 pytest 기반 테스트를 작성해줘.

대상:
- tetris/board.py: is_valid, lock, clear_lines, ghost_y
- tetris/game.py: 점수 계산, 레벨 업, 홀드 로직

GameState는 pygame 비의존이므로 pygame.init() 없이 테스트 가능.
픽스처로 빈 보드, 거의 꽉 찬 보드 등 시나리오를 준비해줘.
```
