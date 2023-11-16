import json
import os
import tempfile
import unittest
from pathlib import Path

from tetris.modes import MODE_LIST
from tetris.profile import ProfileStore, default_data
from tetris.replay import ReplayRecorder


class ProfileStoreTests(unittest.TestCase):
    def test_default_data_has_menu_settings(self):
        data = default_data()
        self.assertIn("theme", data["settings"])
        self.assertIn("mode", data["settings"])
        self.assertIn("bindings", data["settings"])

    def test_load_merges_partial_save_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            path.write_text(
                json.dumps(
                    {
                        "settings": {"theme": "neon"},
                        "stats": {"games_played": 2},
                        "achievements": ["FIRST LINE"],
                    }
                ),
                encoding="utf-8",
            )

            loaded = ProfileStore.load(path)
            self.assertEqual(loaded.settings["theme"], "neon")
            self.assertEqual(loaded.stats["games_played"], 2)
            self.assertIn("bindings", loaded.settings)
            self.assertEqual(sorted(loaded.highscores), ["marathon", "sprint", "time_attack"])
            self.assertEqual(loaded.achievements, ["FIRST LINE"])

    def test_record_run_updates_stats_and_highscores(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            store = ProfileStore.load(path)
            store.record_run("marathon", 12000, 4, 60000, {"tetrises": 1, "t_spins": 2})
            store.save()

            loaded = ProfileStore.load(path)
            self.assertEqual(loaded.stats["games_played"], 1)
            self.assertEqual(loaded.stats["best_score"], 12000)
            self.assertEqual(loaded.stats["tetrises"], 1)
            self.assertEqual(loaded.stats["t_spins"], 2)
            self.assertEqual(len(loaded.highscores["marathon"]), 1)
            self.assertIn("FIRST LINE", loaded.achievements)
            self.assertIn("FIRST TETRIS", loaded.achievements)
            self.assertIn("FIRST T-SPIN", loaded.achievements)
            self.assertIn("10K SCORE", loaded.achievements)

    def test_record_run_sorts_and_trims_highscores(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            store = ProfileStore.load(path)

            for score, elapsed in [(1200, 15000), (1800, 14000), (1500, 14000), (900, 13000)]:
                store.record_run("sprint", score, 40, elapsed)

            self.assertEqual(store.stats["best_sprint_time_ms"], 13000)
            self.assertEqual(store.highscores["sprint"][0]["elapsed_ms"], 13000)
            self.assertEqual(store.highscores["sprint"][0]["score"], 900)

            for offset in range(12):
                store.record_run("marathon", 2000 + offset, 20, 50000 - offset * 1000)

            self.assertEqual(len(store.highscores["marathon"]), 10)
            self.assertEqual(store.highscores["marathon"][0]["score"], 2011)

    def test_theme_and_bgm_cycles_wrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            store = ProfileStore.load(path)

            store.settings["theme"] = "mono"
            self.assertEqual(store.cycle_theme(1), "classic")
            self.assertEqual(store.cycle_theme(-1), "mono")

            tracks = ["track-a.mp3", "track-b.mp3"]
            self.assertEqual(store.cycle_bgm_mode(1, tracks), "off")
            self.assertEqual(store.settings["bgm_mode"], "off")
            self.assertEqual(store.cycle_bgm_mode(1, tracks), "track-a.mp3")
            self.assertEqual(store.settings["bgm_mode"], "selected")
            self.assertEqual(store.settings["bgm_track"], "track-a.mp3")
            self.assertEqual(store.cycle_bgm_mode(1, tracks), "track-b.mp3")
            self.assertEqual(store.cycle_bgm_mode(1, tracks), "random")

    def test_replay_recorder_lists_recent_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old_file = root / "20240101-000000.json"
            new_file = root / "20240102-000000.json"
            bad_file = root / "broken.json"

            old_file.write_text(
                json.dumps(
                    {
                        "metadata": {"mode": "marathon"},
                        "result": {"score": 3210, "lines": 12, "elapsed_ms": 54321},
                    }
                ),
                encoding="utf-8",
            )
            bad_file.write_text("{not json}", encoding="utf-8")
            new_file.write_text(
                json.dumps(
                    {
                        "metadata": {"mode": "time_attack"},
                        "result": {"score": 9999, "lines": 20, "elapsed_ms": 120000},
                    }
                ),
                encoding="utf-8",
            )
            os.utime(old_file, (1, 1))
            os.utime(bad_file, (2, 2))
            os.utime(new_file, (3, 3))

            lines = ReplayRecorder.recent_summaries(limit=5, root=root)
            self.assertEqual(len(lines), 2)
            self.assertIn("TIME_ATTACK", lines[0])
            self.assertIn("9,999 pts", lines[0])
            self.assertIn("MARATHON", lines[1])


class ModeTests(unittest.TestCase):
    def test_modes_exist(self):
        self.assertEqual([mode.slug for mode in MODE_LIST], ["marathon", "sprint", "time_attack"])


if __name__ == "__main__":
    unittest.main()
