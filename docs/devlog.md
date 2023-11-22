# 개발 일지 (Dev Log)

> 날짜별 작업 내용, 막혔던 부분, 배운 것들을 기록한다.

---

## 2023-08-10

### 프로젝트 시작

방학 동안 Python + pygame으로 테트리스를 만들어보기로 했다.
그냥 굴러가는 수준이 아니라 공식 테트리스 가이드라인을 따르는 버전으로.

**참고한 자료**
- The Tetris Guideline (공식 규칙서)
- Tetris Wiki — SRS 회전, 스코어링, DAS/ARR 수치
- pygame 공식 문서

**첫 날 결정 사항**
- 언어: Python 3.9+ + pygame
- 구조: GameState는 pygame 의존 없이 순수 로직만. Renderer가 화면 담당
- 7가지 테트로미노, SRS 회전 시스템, 7-bag 랜덤

---

## 2023-08-18

### 기본 구조 설계

`tetris/` 패키지 구조 확정.

```
tetris/
  config.py   상수 (DAS, ARR, 스코어 등)
  piece.py    테트로미노 모양, 회전
  board.py    그리드, 충돌 감지
  bag.py      7-bag 랜덤
  game.py     게임 상태 관리
  renderer.py pygame 렌더링
  sound.py    효과음
```

`board.py`는 pygame 의존 없이 순수 2D 배열로만 구현.
`game.py`도 마찬가지 — 이렇게 해야 나중에 unittest 짜기 편하다.

**piece.py에서 막힌 부분**
회전을 행렬 변환으로 구현하려다가 공식 SRS 킥 테이블이 따로 있다는 걸 알았다.
I 피스와 나머지 피스의 킥 테이블이 다르다. 공식 문서 보고 직접 하드코딩.

---

## 2023-08-27

### 7-bag 랜덤 구현

`bag.py` — 7개 피스를 랜덤 셔플 후 순서대로 뽑는 방식.
같은 피스가 연속으로 나오지 않도록 보장.

```python
def pop(self) -> int:
    if not self._bag:
        self._bag = list(range(1, 8))
        random.shuffle(self._bag)
    return self._bag.pop()
```

**테스트**
700번 뽑아서 각 피스가 정확히 100번씩 나오는지 확인.

---

## 2023-09-05

### DAS/ARR 입력 처리

Delayed Auto-Shift (DAS): 키를 누르고 있을 때 처음 반응하기까지의 딜레이
Auto-Repeat Rate (ARR): 그 이후 반복 속도

```
DAS_DELAY_MS  = 170ms   (처음 이동 후 반복 시작까지)
ARR_INTERVAL  = 35ms    (반복 간격)
```

공식 기준값이 있어서 그걸 그대로 사용.
처음에 DAS 없이 구현했더니 키 입력이 너무 딱딱해서 게임이 안됨.

**lock delay**
피스가 바닥에 닿은 후 500ms 기다렸다가 고정되도록.
이 사이에 이동하면 lock delay가 리셋됨 (최대 15회).

---

## 2023-09-14

### 스코어 시스템 구현

공식 스코어 공식:
- 1줄: 100 × level
- 2줄: 300 × level
- 3줄: 500 × level
- 4줄 (테트리스): 800 × level
- T-Spin: 400~1600 × level
- Back-to-Back: 1.5배

**T-Spin 감지가 어려웠음**
피스가 회전 후 고정될 때만 유효.
T 피스가 T 위치(코너 3개 이상 막힘)에서 회전 동작으로 고정되어야 함.
`last_move_was_rotation` 플래그 + 코너 체크로 구현.

---

## 2023-09-22

### Combo, Back-to-Back 구현

**콤보**
연속으로 줄을 지우면 콤보 보너스:
- 콤보 1: +50점
- 콤보 N: +50 × N점

**Back-to-Back**
테트리스(4줄) 또는 T-Spin 후 또 테트리스/T-Spin이면 1.5배.
중간에 다른 줄 지우기가 끼면 끊김.

---

## 2023-10-03

### 렌더링 시스템

`renderer.py` — pygame Surface 기반.

그린 것들:
- 메인 게임 보드 (20×10)
- 고스트 블록 (투명하게)
- NEXT 3개 미리보기
- HOLD 블록
- 점수/레벨/줄수 사이드바

**폰트 관리**
크기별로 5가지 폰트 미리 로드. 매 프레임 렌더링 시 생성하면 너무 느려서.

---

## 2023-10-12

### 효과음 합성

pygame 사운드 파일 대신 numpy로 사인파 직접 생성.

```python
t = np.linspace(0, duration, int(44100 * duration))
wave = (np.sin(2 * np.pi * freq * t) * 32767 * 0.3).astype(np.int16)
```

파일 없이 어디서든 소리가 나서 좋다.
이동음 300Hz, 회전음 500Hz, 드롭 150Hz, 줄제거 880Hz.

---

## 2023-10-20

### 게임 모드 추가

- **마라톤**: 제한 없이 계속
- **스프린트 40**: 40줄 가장 빨리 제거
- **타임어택**: 120초 안에 최고 점수

`modes.py`에 dataclass로 정의.
각 모드별 종료 조건이 다르기 때문에 `GameState`에서 체크.

---

## 2023-10-30

### 프로필 저장, 업적 시스템

`profile.py` — JSON 파일로 저장.

저장 항목:
- 통계 (게임 수, 총 줄, 총 점수, T-Spin 수)
- 모드별 최고 점수
- 업적 목록
- 설정 (테마, BGM, 키 바인딩)

업적 6종:
- FIRST LINE, FIRST TETRIS, FIRST T-SPIN
- TEN RUNS, 100 LINES, 10K SCORE

---

## 2023-11-08

### 리플레이 시스템

`replay.py` — 모든 키 입력을 타임스탬프와 함께 JSON으로 저장.

```json
{
  "mode": "marathon",
  "seed": 12345,
  "start_level": 1,
  "actions": [
    {"t": 120, "key": "move_left"},
    {"t": 240, "key": "rotate"}
  ],
  "final_score": 4800,
  "lines": 12
}
```

같은 seed + 같은 액션 = 동일한 게임 재현 가능.

---

## 2023-11-15

### AI 데모 모드 구현

타이틀 화면에서 AI가 자동으로 플레이하는 데모 모드.

처음엔 랜덤 액션으로 구현했는데 너무 금방 죽어서 다시 만들었다.

**Dellacherie 휴리스틱**
각 배치 후 보드 상태를 평가:
- aggregate_height: 전체 열 높이 합 (낮을수록 좋음)
- complete_lines: 완성된 줄 수 (많을수록 좋음)
- holes: 구멍 수 (적을수록 좋음)
- bumpiness: 인접 열 높이 차이 (낮을수록 좋음)

가중치: `score = -0.51 * height + 0.76 * lines - 0.36 * holes - 0.18 * bumpy`

논문에서 찾은 가중치인데 실제로 꽤 잘 됨.

---

## 2023-11-22

### 테스트 추가, 버그 수정, 최종 정리

**버그 수정**
- `main.py`에서 `_achievement_lines`, `_replay_lines` 등 함수 4개가 중복 정의된 것 발견 → 제거
- 메뉴 이동 시 BGM이 재시작되는 버그 수정

**테스트 추가**
- `test_bag.py`: 7-bag 분포 검증, peek 동작 확인
- `test_board.py`: 충돌 감지, 줄 제거, 고스트 Y 계산

**아쉬운 점**
- T-Spin Mini 감지 미구현 (config에 상수는 있음)
- 리플레이 재생 뷰어 미완성
- 멀티플레이 없음

**다음에 해보고 싶은 것**
- 온라인 대전 (socket)
- 리플레이 실시간 재생
- 더 정교한 AI (강화학습?)
