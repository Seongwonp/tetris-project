"""Tetris 게임 진입점 – 메뉴, 설정, 플레이, 결과 화면."""

import random
import sys
from typing import Dict, Optional, List, Tuple

import pygame

from tetris.game import GameState
from tetris.modes import MODE_LIST, MODE_BY_SLUG, MARATHON, GameMode
from tetris.profile import ProfileStore, default_bindings, default_data
from tetris.renderer import Renderer, SCREEN_W, SCREEN_H, apply_theme
from tetris.replay import ReplayRecorder
from tetris.sound import SoundManager
from tetris.themes import THEMES, THEME_LIST

FPS = 60
TITLE_MENU = ["START", "MODE", "SETTINGS", "SCORES", "REPLAYS", "ACHIEVEMENTS", "QUIT"]
SETTINGS_MENU = ["THEME", "BGM", "KEY BINDINGS", "RESET DATA", "BACK"]
KEY_ACTIONS = ["left", "right", "rotate", "down", "hard_drop", "hold", "pause", "restart", "mute"]
KEY_LABELS = {
    "left": "Move Left",
    "right": "Move Right",
    "rotate": "Rotate",
    "down": "Soft Drop",
    "hard_drop": "Hard Drop",
    "hold": "Hold",
    "pause": "Pause",
    "restart": "Restart",
    "mute": "Mute",
}


def main() -> None:
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("TETRIS")
    pygame.key.set_repeat(160, 55)

    profile = ProfileStore.load()
    profile.settings.setdefault("bindings", default_bindings())
    profile.settings.setdefault("theme", "classic")
    profile.settings.setdefault("mode", "marathon")
    profile.settings.setdefault("start_level", 1)
    profile.settings.setdefault("bgm_mode", "random")
    profile.settings.setdefault("bgm_track", "")
    profile.settings.setdefault("sound_enabled", True)

    theme = THEMES.get(profile.settings["theme"], THEMES["classic"])
    apply_theme(theme)

    sound = SoundManager()
    sound.set_preferences(
        bool(profile.settings.get("sound_enabled", True)),
        profile.settings.get("bgm_mode", "random"),
        profile.settings.get("bgm_track", ""),
        restart_bgm=True,
    )
    sound.play_bgm()

    state = GameState(on_sound=sound.play)
    demo_state = GameState()
    renderer = Renderer(screen)
    clock = pygame.time.Clock()

    app_state = "title"
    title_index = 0
    mode_index = _mode_index(profile.settings.get("mode", "marathon"))
    settings_index = 0
    keybind_index = 0
    waiting_binding: Optional[str] = None
    result_index = 0
    selected_mode = MODE_BY_SLUG.get(profile.settings.get("mode", "marathon"), MARATHON)
    start_level = int(profile.settings.get("start_level", 1))
    demo_action_acc = 0
    replay: Optional[ReplayRecorder] = None
    replay_path: Optional[str] = None
    run_saved = False

    while True:
        dt = clock.tick(FPS)

        if app_state in ("title", "mode", "settings", "keybind", "scores", "replays", "achievements"):
            demo_action_acc = _update_demo(demo_state, dt, demo_action_acc, start_level)
        elif app_state == "game":
            if replay:
                replay.tick(dt)
            state.update(dt)
            if state.game_over and not run_saved:
                replay_path = _finish_run(profile, state, selected_mode, replay)
                run_saved = True
                app_state = "result"
                result_index = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                profile.save()
                pygame.quit()
                sys.exit()

            if app_state == "title":
                title_index, app_state, selected_mode, start_level, replay, run_saved, replay_path = _handle_title_event(
                    event,
                    profile,
                    sound,
                    state,
                    demo_state,
                    title_index,
                    mode_index,
                    start_level,
                )
                mode_index = _mode_index(profile.settings.get("mode", "marathon"))
            elif app_state == "mode":
                mode_index, start_level, app_state, selected_mode = _handle_mode_event(
                    event,
                    profile,
                    mode_index,
                    start_level,
                )
            elif app_state == "settings":
                settings_index, keybind_index, waiting_binding, app_state = _handle_settings_event(
                    event,
                    profile,
                    sound,
                    settings_index,
                    keybind_index,
                    waiting_binding,
                )
                theme = THEMES.get(profile.settings["theme"], theme)
                apply_theme(theme)
                sound.set_preferences(
                    bool(profile.settings.get("sound_enabled", True)),
                    profile.settings.get("bgm_mode", "random"),
                    profile.settings.get("bgm_track", ""),
                    restart_bgm=False,
                )
                selected_mode = MODE_BY_SLUG.get(profile.settings.get("mode", "marathon"), MARATHON)
                mode_index = _mode_index(profile.settings.get("mode", "marathon"))
                start_level = int(profile.settings.get("start_level", 1))
            elif app_state == "keybind":
                keybind_index, waiting_binding, app_state = _handle_keybind_event(
                    event,
                    profile,
                    sound,
                    keybind_index,
                    waiting_binding,
                )
            elif app_state == "scores":
                if _any_back_key(event):
                    app_state = "title"
            elif app_state == "replays":
                if _any_back_key(event):
                    app_state = "title"
            elif app_state == "achievements":
                if _any_back_key(event):
                    app_state = "title"
            elif app_state == "game":
                _handle_game_event(event, profile, sound, state, selected_mode, start_level, replay)
            elif app_state == "result":
                result_index, app_state, replay_path, replay, run_saved = _handle_result_event(
                    event,
                    profile,
                    sound,
                    state,
                    selected_mode,
                    result_index,
                    start_level,
                    replay_path,
                    replay,
                )

        if app_state == "title":
            renderer.draw_title_menu(
                demo_state,
                title_index,
                selected_mode.title,
                theme.title,
                _bgm_label(profile, sound),
                (pygame.time.get_ticks() // 450) % 2 == 0,
            )
        elif app_state == "mode":
            renderer.draw_mode_menu(demo_state, mode_index, start_level)
        elif app_state == "settings":
            renderer.draw_settings_menu(demo_state, _settings_lines(profile, sound), settings_index, waiting_binding is not None)
        elif app_state == "keybind":
            renderer.draw_settings_menu(demo_state, _keybind_lines(profile), keybind_index, waiting_binding is not None)
        elif app_state == "scores":
            renderer.draw_scores_menu(demo_state, _score_lines(profile), _score_footer_lines(profile))
        elif app_state == "replays":
            renderer.draw_info_menu(demo_state, "REPLAYS", _replay_lines(), _replay_footer_lines())
        elif app_state == "achievements":
            renderer.draw_info_menu(demo_state, "ACHIEVEMENTS", _achievement_lines(profile), _achievement_footer_lines(profile))
        elif app_state == "game":
            renderer.draw(state)
        elif app_state == "result":
            renderer.draw_result_menu(state, "RESULT", _result_lines(state, selected_mode, replay_path), ["RETRY", "MENU"], result_index)


def _handle_title_event(event: pygame.event.Event, profile: ProfileStore, sound: SoundManager,
                        state: GameState, demo_state: GameState, title_index: int,
                        mode_index: int, start_level: int) -> Tuple[int, str, GameMode, int, Optional[ReplayRecorder], bool, Optional[str]]:
    selected_mode = MODE_BY_SLUG.get(profile.settings.get("mode", "marathon"), MARATHON)
    replay = None
    run_saved = False
    replay_path = None
    app_state = "title"

    if event.type != pygame.KEYDOWN:
        return title_index, app_state, selected_mode, start_level, replay, run_saved, replay_path

    if event.key == pygame.K_UP:
        title_index = (title_index - 1) % len(TITLE_MENU)
    elif event.key == pygame.K_DOWN:
        title_index = (title_index + 1) % len(TITLE_MENU)
    elif event.key == pygame.K_m:
        profile.settings["sound_enabled"] = not bool(profile.settings.get("sound_enabled", True))
        sound.set_preferences(
            bool(profile.settings["sound_enabled"]),
            profile.settings.get("bgm_mode", "random"),
            profile.settings.get("bgm_track", ""),
            restart_bgm=True,
        )
        profile.save()
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
        choice = TITLE_MENU[title_index]
        if choice == "START":
            start_level = int(profile.settings.get("start_level", 1))
            selected_mode = MODE_BY_SLUG.get(profile.settings.get("mode", "marathon"), MARATHON)
            seed = random.randint(0, 2 ** 31 - 1)
            state.reset(start_level=start_level, mode=selected_mode, seed=seed)
            replay = ReplayRecorder.create(
                {
                    "mode": selected_mode.slug,
                    "start_level": start_level,
                    "seed": seed,
                    "theme": profile.settings.get("theme"),
                    "bgm_mode": profile.settings.get("bgm_mode"),
                    "bgm_track": profile.settings.get("bgm_track"),
                }
            )
            replay.record("start")
            app_state = "game"
        elif choice == "MODE":
            app_state = "mode"
        elif choice == "SETTINGS":
            app_state = "settings"
        elif choice == "SCORES":
            app_state = "scores"
        elif choice == "REPLAYS":
            app_state = "replays"
        elif choice == "ACHIEVEMENTS":
            app_state = "achievements"
        elif choice == "QUIT":
            profile.save()
            pygame.quit()
            sys.exit()

    return title_index, app_state, selected_mode, start_level, replay, run_saved, replay_path


def _handle_mode_event(event: pygame.event.Event, profile: ProfileStore, mode_index: int,
                       start_level: int) -> Tuple[int, int, str, GameMode]:
    app_state = "mode"
    selected_mode = MODE_BY_SLUG.get(profile.settings.get("mode", "marathon"), MARATHON)
    if event.type != pygame.KEYDOWN:
        return mode_index, start_level, app_state, selected_mode

    if event.key == pygame.K_ESCAPE:
        app_state = "title"
    elif event.key == pygame.K_UP:
        mode_index = (mode_index - 1) % len(MODE_LIST)
    elif event.key == pygame.K_DOWN:
        mode_index = (mode_index + 1) % len(MODE_LIST)
    elif event.key == pygame.K_LEFT:
        start_level = max(1, start_level - 1)
    elif event.key == pygame.K_RIGHT:
        start_level = min(10, start_level + 1)
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        selected_mode = MODE_LIST[mode_index]
        profile.settings["mode"] = selected_mode.slug
        profile.settings["start_level"] = start_level
        profile.save()
        app_state = "title"
    if app_state == "title":
        selected_mode = MODE_BY_SLUG.get(profile.settings.get("mode", "marathon"), MARATHON)
    else:
        selected_mode = MODE_LIST[mode_index]
    return mode_index, start_level, app_state, selected_mode


def _handle_settings_event(event: pygame.event.Event, profile: ProfileStore, sound: SoundManager,
                           settings_index: int, keybind_index: int, waiting_binding: Optional[str]) -> Tuple[int, int, Optional[str], str]:
    app_state = "settings"
    if event.type != pygame.KEYDOWN:
        return settings_index, keybind_index, waiting_binding, app_state

    theme_list = [theme.slug for theme in THEME_LIST]
    bgm_options = ["random", "off"] + sound.track_names()

    if event.key == pygame.K_ESCAPE:
        app_state = "title"
    elif event.key == pygame.K_UP:
        settings_index = (settings_index - 1) % len(SETTINGS_MENU)
    elif event.key == pygame.K_DOWN:
        settings_index = (settings_index + 1) % len(SETTINGS_MENU)
    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
        direction = -1 if event.key == pygame.K_LEFT else 1
        if settings_index == 0:
            current = profile.settings.get("theme", "classic")
            index = theme_list.index(current) if current in theme_list else 0
            profile.settings["theme"] = theme_list[(index + direction) % len(theme_list)]
        elif settings_index == 1 and bgm_options:
            current_mode = profile.settings.get("bgm_mode", "random")
            current_track = profile.settings.get("bgm_track", "")
            current = current_track if current_mode == "selected" else current_mode
            index = bgm_options.index(current) if current in bgm_options else 0
            choice = bgm_options[(index + direction) % len(bgm_options)]
            if choice in ("random", "off"):
                profile.settings["bgm_mode"] = choice
                profile.settings["bgm_track"] = ""
            else:
                profile.settings["bgm_mode"] = "selected"
                profile.settings["bgm_track"] = choice
            sound.set_preferences(
                bool(profile.settings.get("sound_enabled", True)),
                profile.settings.get("bgm_mode", "random"),
                profile.settings.get("bgm_track", ""),
                restart_bgm=True,
            )
        profile.save()
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        if settings_index == 2:
            app_state = "keybind"
        elif settings_index == 3:
            profile.data = default_data()
            profile.save()
            sound.set_preferences(
                bool(profile.settings.get("sound_enabled", True)),
                profile.settings.get("bgm_mode", "random"),
                profile.settings.get("bgm_track", ""),
                restart_bgm=True,
            )
        elif settings_index == 4:
            app_state = "title"
    return settings_index, keybind_index, waiting_binding, app_state


def _handle_keybind_event(event: pygame.event.Event, profile: ProfileStore, sound: SoundManager,
                          keybind_index: int, waiting_binding: Optional[str]) -> Tuple[int, Optional[str], str]:
    app_state = "keybind"
    bindings = profile.settings.setdefault("bindings", default_bindings())
    if event.type == pygame.KEYDOWN:
        if waiting_binding:
            if event.key != pygame.K_ESCAPE:
                bindings[waiting_binding] = event.key
                profile.save()
            waiting_binding = None
        elif event.key == pygame.K_ESCAPE:
            app_state = "settings"
        elif event.key == pygame.K_UP:
            keybind_index = (keybind_index - 1) % len(KEY_ACTIONS)
        elif event.key == pygame.K_DOWN:
            keybind_index = (keybind_index + 1) % len(KEY_ACTIONS)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            waiting_binding = KEY_ACTIONS[keybind_index]
        elif event.key == bindings.get("mute"):
            profile.settings["sound_enabled"] = not bool(profile.settings.get("sound_enabled", True))
            sound.set_preferences(
                bool(profile.settings["sound_enabled"]),
                profile.settings.get("bgm_mode", "random"),
                profile.settings.get("bgm_track", ""),
                restart_bgm=True,
            )
            profile.save()
    return keybind_index, waiting_binding, app_state


def _handle_game_event(event: pygame.event.Event, profile: ProfileStore, sound: SoundManager,
                       state: GameState, selected_mode: GameMode, start_level: int,
                       replay: Optional[ReplayRecorder]) -> None:
    bindings = profile.settings.get("bindings", default_bindings())
    if event.type == pygame.KEYUP:
        if event.key == bindings.get("left"):
            state.release_left()
        elif event.key == bindings.get("right"):
            state.release_right()
        elif event.key == bindings.get("down"):
            state.release_down()
        return

    if event.type != pygame.KEYDOWN:
        return

    action = _action_for_key(event.key, bindings)
    if replay and action:
        replay.record(action, event.key)

    if state.game_over:
        return

    if action == "restart":
        state.reset(start_level=start_level, mode=selected_mode, seed=random.randint(0, 2 ** 31 - 1))
    elif action == "pause":
        state.toggle_pause()
    elif action == "left":
        state.press_left()
    elif action == "right":
        state.press_right()
    elif action == "rotate":
        state.rotate()
    elif action == "down":
        state.press_down()
    elif action == "hard_drop":
        state.hard_drop()
    elif action == "hold":
        state.hold()
    elif action == "mute":
        profile.settings["sound_enabled"] = not bool(profile.settings.get("sound_enabled", True))
        sound.set_preferences(
            bool(profile.settings["sound_enabled"]),
            profile.settings.get("bgm_mode", "random"),
            profile.settings.get("bgm_track", ""),
            restart_bgm=True,
        )
        profile.save()
    elif event.key == pygame.K_ESCAPE:
        state.game_over = True
        state.result_reason = "ABORTED"


def _handle_result_event(event: pygame.event.Event, profile: ProfileStore, sound: SoundManager,
                         state: GameState, selected_mode: GameMode, result_index: int,
                         start_level: int, replay_path: Optional[str],
                         replay: Optional[ReplayRecorder]) -> Tuple[int, str, Optional[str], Optional[ReplayRecorder], bool]:
    app_state = "result"
    if event.type != pygame.KEYDOWN:
        return result_index, app_state, replay_path, replay, False

    if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
        result_index = 1 - result_index
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
        if result_index == 0:
            seed = random.randint(0, 2 ** 31 - 1)
            state.reset(start_level=start_level, mode=selected_mode, seed=seed)
            replay = ReplayRecorder.create(
                {
                    "mode": selected_mode.slug,
                    "start_level": start_level,
                    "seed": seed,
                    "theme": profile.settings.get("theme"),
                    "bgm_mode": profile.settings.get("bgm_mode"),
                    "bgm_track": profile.settings.get("bgm_track"),
                }
            )
            replay.record("start")
            app_state = "game"
            replay_path = None
            return result_index, app_state, replay_path, replay, False
        else:
            app_state = "title"
            replay = None
            replay_path = None
            return result_index, app_state, replay_path, replay, False
    elif event.key == pygame.K_ESCAPE:
        app_state = "title"
    elif event.key == pygame.K_m:
        profile.settings["sound_enabled"] = not bool(profile.settings.get("sound_enabled", True))
        sound.set_preferences(
            bool(profile.settings["sound_enabled"]),
            profile.settings.get("bgm_mode", "random"),
            profile.settings.get("bgm_track", ""),
            restart_bgm=True,
        )
        profile.save()
    return result_index, app_state, replay_path, replay, False


def _finish_run(profile: ProfileStore, state: GameState, selected_mode: GameMode,
                replay: Optional[ReplayRecorder]) -> Optional[str]:
    extras = {"tetrises": state.tetrises, "t_spins": state.t_spins}
    profile.record_run(selected_mode.slug, state.score, state.lines, state.elapsed_ms, extras)
    profile.save()
    if replay:
        return str(replay.save({
            "mode": selected_mode.slug,
            "score": state.score,
            "lines": state.lines,
            "elapsed_ms": state.elapsed_ms,
            "reason": state.result_reason or "GAME OVER",
        }))
    return None


def _action_for_key(key: int, bindings: Dict[str, int]) -> Optional[str]:
    reverse = {value: action for action, value in bindings.items()}
    return reverse.get(key)


def _mode_index(mode_slug: str) -> int:
    for index, mode in enumerate(MODE_LIST):
        if mode.slug == mode_slug:
            return index
    return 0


def _bgm_label(profile: ProfileStore, sound: SoundManager) -> str:
    mode = profile.settings.get("bgm_mode", "random")
    if mode == "off":
        return "Off"
    if mode == "selected":
        return profile.settings.get("bgm_track", "") or "Random"
    return "Random"


def _settings_lines(profile: ProfileStore, sound: SoundManager) -> List[str]:
    bindings = profile.settings.get("bindings", default_bindings())
    return [
        f"THEME: {THEMES.get(profile.settings.get('theme', 'classic'), THEMES['classic']).title}",
        f"BGM: {_bgm_label(profile, sound)}",
        "KEY BINDINGS",
        "RESET DATA",
        "BACK",
    ]


def _keybind_lines(profile: ProfileStore) -> List[str]:
    bindings = profile.settings.get("bindings", default_bindings())
    lines = []
    for action in KEY_ACTIONS:
        key = bindings.get(action)
        name = pygame.key.name(key).upper() if isinstance(key, int) else "-"
        lines.append(f"{KEY_LABELS[action]}: {name}")
    return lines


def _score_lines(profile: ProfileStore) -> List[str]:
    highscores = profile.highscores
    lines = []
    for mode in ["marathon", "sprint", "time_attack"]:
        entries = highscores.get(mode, [])[:3]
        if not entries:
            lines.append(f"{MODE_BY_SLUG[mode].title}: --")
            continue
        summary = ", ".join(
            f"{item['score']:,}/{int(item['elapsed_ms']) // 1000}s" for item in entries
        )
        lines.append(f"{MODE_BY_SLUG[mode].title}: {summary}")
    return lines


def _score_footer_lines(profile: ProfileStore) -> List[str]:
    stats = profile.stats
    return [
        f"RUNS {stats['games_played']}  LINES {stats['total_lines']}  SCORE {stats['total_score']:,}",
        f"BEST {stats['best_score']:,}  MARATHON {stats['best_marathon_score']:,}",
        f"TETRISES {stats['tetrises']}  T-SPINS {stats['t_spins']}  ACHIEVEMENTS {len(profile.achievements)}",
    ]


def _achievement_lines(profile: ProfileStore) -> List[str]:
    unlocked = profile.achievements
    if not unlocked:
        return [
            "NO ACHIEVEMENTS YET",
            "CLEAR LINES, PLAY MORE,",
            "AND TRY DIFFERENT MODES",
        ]
    return [f"[X] {item}" for item in unlocked]


def _achievement_footer_lines(profile: ProfileStore) -> List[str]:
    stats = profile.stats
    return [
        f"UNLOCKED {len(profile.achievements)} / 6",
        f"GAMES {stats['games_played']}  LINES {stats['total_lines']}  SCORE {stats['total_score']:,}",
        "FIRST LINE  FIRST TETRIS  FIRST T-SPIN  10K SCORE",
    ]


def _replay_lines() -> List[str]:
    lines = ReplayRecorder.recent_summaries(limit=6)
    if not lines:
        return [
            "NO REPLAYS SAVED YET",
            "FINISH A RUN TO RECORD",
            "A JSON FILE WILL APPEAR",
        ]
    return lines


def _replay_footer_lines() -> List[str]:
    return [
        "ENTER / ESC TO GO BACK",
        f"SAVED TO {ReplayRecorder.default_root()}",
    ]


def _result_lines(state: GameState, selected_mode: GameMode, replay_path: Optional[str]) -> List[str]:
    elapsed = max(0, state.elapsed_ms // 1000)
    lines = [
        f"MODE: {selected_mode.title}",
        f"SCORE: {state.score:,}",
        f"LINES: {state.lines}",
        f"TIME: {elapsed}s",
        f"RESULT: {state.result_reason or 'DONE'}",
    ]
    if replay_path:
        lines.append(f"REPLAY SAVED")
    return lines


def _any_back_key(event: pygame.event.Event) -> bool:
    return event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


def _update_demo(state: GameState, dt: int, action_acc: int, start_level: int) -> int:
    if state.game_over:
        state.reset(start_level=start_level, mode=MARATHON)
        return 0
    state.update(dt)
    action_acc += dt
    if action_acc >= 140:
        action_acc = 0
        roll = random.random()
        if roll < 0.4:
            state.move(random.choice((-1, 1)))
        elif roll < 0.6:
            state.rotate()
        elif roll < 0.92:
            state.soft_drop()
        else:
            state.hard_drop()
    return action_acc


if __name__ == "__main__":
    main()
