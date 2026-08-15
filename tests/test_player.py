import json
import os
import tempfile
from unittest.mock import MagicMock, call, patch

import numpy as np
import pytest

from engine.player import Player, PlayerResult


class TestPlayerResult:
    def test_player_result_creation(self):
        result = PlayerResult(completed_cycles=3, total_time_ms=15000, stopped_early=False)
        assert result.completed_cycles == 3
        assert result.total_time_ms == 15000
        assert result.stopped_early is False

    def test_player_result_stopped_early(self):
        result = PlayerResult(completed_cycles=0, total_time_ms=500, stopped_early=True)
        assert result.completed_cycles == 0
        assert result.stopped_early is True

    def test_player_result_defaults(self):
        result = PlayerResult()
        assert result.completed_cycles == 0
        assert result.total_time_ms == 0
        assert result.stopped_early is False


class TestPlayerInit:
    def _make_script_dir(self, tmpdir, events=None):
        if events is None:
            events = [
                {
                    "type": "key",
                    "action": "down",
                    "delay_ms": 100,
                    "key": "a",
                    "keycode": 65,
                },
                {
                    "type": "key",
                    "action": "up",
                    "delay_ms": 50,
                    "key": "a",
                    "keycode": 65,
                },
            ]
        data = {
            "version": 1,
            "meta": {
                "created": "2026-08-12T14:30:00",
                "screen": [1920, 1080],
                "duration_ms": 150,
                "event_count": len(events),
            },
            "events": events,
        }
        script_path = os.path.join(tmpdir, "script.json")
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return tmpdir

    def test_player_init_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir)
            assert player._times == 1
            assert player._speed == 1.0
            assert player._use_match is False
            assert player._script is not None
            assert len(player._script.events) == 2

    def test_player_init_with_options(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, times=5, speed=2.0, use_match=False)
            assert player._times == 5
            assert player._speed == 2.0
            assert player._use_match is False

    def test_player_init_script_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                Player(tmpdir)

    def test_player_init_speed_zero_clamped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, speed=0)
            assert player._speed == 0.01

    def test_player_init_negative_speed_clamped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, speed=-1.0)
            assert player._speed == 0.01


class TestCoordinateConversion:
    def _make_script_dir(self, tmpdir):
        data = {
            "version": 1,
            "meta": {
                "created": "2026-08-12T14:30:00",
                "screen": [1920, 1080],
                "duration_ms": 10,
                "event_count": 1,
            },
            "events": [
                {
                    "type": "mouse",
                    "action": "move",
                    "delay_ms": 10,
                    "pos": [0.5, 0.5],
                }
            ],
        }
        script_path = os.path.join(tmpdir, "script.json")
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return tmpdir

    def test_rel_to_abs_center(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir)
            x, y = player._rel_to_abs([0.5, 0.5], 1920, 1080)
            assert x == 960
            assert y == 540

    def test_rel_to_abs_top_left(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir)
            x, y = player._rel_to_abs([0.0, 0.0], 1920, 1080)
            assert x == 0
            assert y == 0

    def test_rel_to_abs_bottom_right(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir)
            x, y = player._rel_to_abs([1.0, 1.0], 1920, 1080)
            assert x == 1920
            assert y == 1080


class TestDelayCalculation:
    def _make_script_dir(self, tmpdir):
        data = {
            "version": 1,
            "meta": {
                "created": "2026-08-12T14:30:00",
                "screen": [1920, 1080],
                "duration_ms": 10,
                "event_count": 1,
            },
            "events": [
                {
                    "type": "key",
                    "action": "down",
                    "delay_ms": 100,
                    "key": "a",
                    "keycode": 65,
                }
            ],
        }
        script_path = os.path.join(tmpdir, "script.json")
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return tmpdir

    def test_calc_delay_normal_speed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, speed=1.0)
            assert player._calc_delay(100) == 100

    def test_calc_delay_double_speed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, speed=2.0)
            assert player._calc_delay(200) == 100

    def test_calc_delay_half_speed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, speed=0.5)
            assert player._calc_delay(100) == 200

    def test_calc_delay_minimum_one_ms(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, speed=100.0)
            assert player._calc_delay(10) == 1


class TestPosMatch:
    def _make_script_dir(self, tmpdir, events=None):
        if events is None:
            events = [
                {
                    "type": "mouse",
                    "action": "click",
                    "delay_ms": 10,
                    "pos": [0.5, 0.5],
                    "shot": "shots/0001.png",
                }
            ]
        data = {
            "version": 1,
            "meta": {
                "created": "2026-08-12T14:30:00",
                "screen": [1920, 1080],
                "duration_ms": 10,
                "event_count": len(events),
            },
            "events": events,
        }
        script_path = os.path.join(tmpdir, "script.json")
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return tmpdir

    def test_pos_match_nomatch_uses_original_coords(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, use_match=False)
            event = player._script.events[0]
            x, y = player._pos_match(event, 1920, 1080)
            assert x == 960
            assert y == 540

    def test_pos_match_no_shot_uses_original_coords(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            events = [
                {
                    "type": "mouse",
                    "action": "click",
                    "delay_ms": 10,
                    "pos": [0.5, 0.5],
                    "shot": None,
                }
            ]
            self._make_script_dir(tmpdir, events)
            player = Player(tmpdir, use_match=True)
            event = player._script.events[0]
            x, y = player._pos_match(event, 1920, 1080)
            assert x == 960
            assert y == 540

    def test_pos_match_direct_hit_at_offset(self):
        """尝试 1: 在 offset+原始坐标直接命中"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events = [
                {
                    "type": "mouse",
                    "action": "click",
                    "delay_ms": 10,
                    "pos": [0.5, 0.5],
                    "shot": "shots/0001.png",
                }
            ]
            self._make_script_dir(tmpdir, events)
            player = Player(tmpdir, use_match=True)
            player._offset = (10, -5)

            dummy_shot = np.zeros((50, 50), dtype=np.float64)
            dummy_screen = np.zeros((200, 200), dtype=np.float64)

            with patch.object(player, "_load_shot", return_value=dummy_shot), \
                 patch.object(player, "_capture_screen", return_value=dummy_screen), \
                 patch("engine.player.match_template", return_value=((975, 535), 0.95)):
                event = player._script.events[0]
                x, y = player._pos_match(event, 1920, 1080)
                assert x == 975
                assert y == 535
                assert player._offset == (975 - 960, 535 - 540)

    def test_pos_match_fallback_to_original(self):
        """尝试 1 失败，尝试 2 在原始坐标命中"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events = [
                {
                    "type": "mouse",
                    "action": "click",
                    "delay_ms": 10,
                    "pos": [0.5, 0.5],
                    "shot": "shots/0001.png",
                }
            ]
            self._make_script_dir(tmpdir, events)
            player = Player(tmpdir, use_match=True)
            player._offset = (100, 100)  # 过时的 offset

            dummy_shot = np.zeros((50, 50), dtype=np.float64)
            dummy_screen = np.zeros((200, 200), dtype=np.float64)

            call_count = [0]

            def mock_match(screen, tpl, pos, radius, conf):
                call_count[0] += 1
                if call_count[0] == 1:
                    return None  # 尝试 1 失败
                return ((960, 540), 0.90)  # 尝试 2 命中

            with patch.object(player, "_load_shot", return_value=dummy_shot), \
                 patch.object(player, "_capture_screen", return_value=dummy_screen), \
                 patch("engine.player.match_template", side_effect=mock_match):
                event = player._script.events[0]
                x, y = player._pos_match(event, 1920, 1080)
                assert x == 960
                assert y == 540
                assert player._offset == (0, 0)
                assert call_count[0] == 2

    def test_pos_match_fullscreen_fallback(self):
        """尝试 1、2 失败，尝试 3 全屏命中"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events = [
                {
                    "type": "mouse",
                    "action": "click",
                    "delay_ms": 10,
                    "pos": [0.5, 0.5],
                    "shot": "shots/0001.png",
                }
            ]
            self._make_script_dir(tmpdir, events)
            player = Player(tmpdir, use_match=True)

            dummy_shot = np.zeros((50, 50), dtype=np.float64)
            dummy_screen = np.zeros((200, 200), dtype=np.float64)

            call_count = [0]

            def mock_match(screen, tpl, pos, radius, conf):
                call_count[0] += 1
                if call_count[0] <= 2:
                    return None  # 尝试 1、2 失败
                return ((1200, 600), 0.88)  # 尝试 3 命中

            with patch.object(player, "_load_shot", return_value=dummy_shot), \
                 patch.object(player, "_capture_screen", return_value=dummy_screen), \
                 patch("engine.player.match_template", side_effect=mock_match):
                event = player._script.events[0]
                x, y = player._pos_match(event, 1920, 1080)
                assert x == 1200
                assert y == 600
                assert player._offset == (1200 - 960, 600 - 540)
                assert call_count[0] == 3

    def test_pos_match_all_fail_fallback(self):
        """三档全失败，兜底返回原始坐标+offset"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events = [
                {
                    "type": "mouse",
                    "action": "click",
                    "delay_ms": 10,
                    "pos": [0.5, 0.5],
                    "shot": "shots/0001.png",
                }
            ]
            self._make_script_dir(tmpdir, events)
            player = Player(tmpdir, use_match=True)
            player._offset = (5, 5)

            dummy_shot = np.zeros((50, 50), dtype=np.float64)
            dummy_screen = np.zeros((200, 200), dtype=np.float64)

            with patch.object(player, "_load_shot", return_value=dummy_shot), \
                 patch.object(player, "_capture_screen", return_value=dummy_screen), \
                 patch("engine.player.match_template", return_value=None):
                event = player._script.events[0]
                x, y = player._pos_match(event, 1920, 1080)
                assert x == 965   # 960 + 5
                assert y == 545   # 540 + 5
                assert player._offset == (5, 5)  # offset 不变

    def test_pos_match_no_shot_uses_offset(self):
        """无 shot 事件：返回原始坐标 + offset"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events = [
                {
                    "type": "mouse",
                    "action": "move",
                    "delay_ms": 10,
                    "pos": [0.4, 0.6],
                    "shot": None,
                }
            ]
            self._make_script_dir(tmpdir, events)
            player = Player(tmpdir, use_match=True)
            player._offset = (20, -10)

            event = player._script.events[0]
            x, y = player._pos_match(event, 1920, 1080)
            assert x == 768 + 20  # 0.4*1920 + 20
            assert y == 648 - 10  # 0.6*1080 - 10

    def test_pos_match_use_match_false(self):
        """use_match=False: 返回原始坐标 + offset，不搜图"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events = [
                {
                    "type": "mouse",
                    "action": "click",
                    "delay_ms": 10,
                    "pos": [0.5, 0.5],
                    "shot": "shots/0001.png",
                }
            ]
            self._make_script_dir(tmpdir, events)
            player = Player(tmpdir, use_match=False)
            player._offset = (10, 10)

            event = player._script.events[0]
            x, y = player._pos_match(event, 1920, 1080)
            assert x == 970
            assert y == 550

    def test_offset_reset_per_cycle(self):
        """每个循环开始时 offset 重置为 (0,0)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events = [
                {
                    "type": "key",
                    "action": "down",
                    "delay_ms": 10,
                    "key": "a",
                    "keycode": 65,
                }
            ]
            self._make_script_dir(tmpdir, events)
            player = Player(tmpdir, use_match=False)
            player._offset = (999, 999)

            stop_calls = [0]

            def mock_check_stop():
                stop_calls[0] += 1
                return stop_calls[0] > 1  # 第一次 False 进入循环，第二次 True 退出

            with patch.object(player, "_start_stop_listener"), \
                 patch.object(player, "_stop_listener"), \
                 patch.object(player, "_check_stop", side_effect=mock_check_stop):
                result = player.play()
                assert player._offset == (0, 0)


class TestCompressedPlayback:
    def _make_script_dir(self, tmpdir, events=None):
        if events is None:
            events = [
                {
                    "type": "mouse",
                    "action": "move",
                    "delay_ms": 500,
                    "pos": [0.1, 0.1],
                    "positions": [[0.1, 0.1], [0.2, 0.2], [0.3, 0.3]],
                },
                {
                    "type": "mouse",
                    "action": "left_down",
                    "delay_ms": 100,
                    "pos": [0.3, 0.3],
                },
            ]
        data = {
            "version": 1,
            "meta": {
                "created": "2026-08-14T10:00:00",
                "screen": [1920, 1080],
                "duration_ms": 600,
                "event_count": len(events),
            },
            "events": events,
        }
        script_path = os.path.join(tmpdir, "script.json")
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return tmpdir

    @patch("engine.player.win32api.SetCursorPos")
    @patch("engine.player.time.sleep")
    @patch("engine.player.ImageGrab.grab")
    def test_compressed_move_expands_to_multiple_mouse_events(self, mock_grab, mock_sleep, mock_setcursor):
        from PIL import Image
        mock_grab.return_value = Image.new("RGB", (1920, 1080))
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, use_match=False)
            player._start_stop_listener = MagicMock()
            player._stop_listener = MagicMock()
            player._check_stop = MagicMock(return_value=False)
            player._stop_flag = False

            player.play()

            assert mock_setcursor.call_count >= 4
            assert mock_setcursor.call_args_list[0] == call((192, 108),)
            assert mock_setcursor.call_args_list[1] == call((384, 216),)
            assert mock_setcursor.call_args_list[2] == call((576, 324),)

    @patch("engine.player.win32api.SetCursorPos")
    @patch("engine.player.time.sleep")
    @patch("engine.player.ImageGrab.grab")
    def test_compressed_drag_uses_delays(self, mock_grab, mock_sleep, mock_setcursor):
        from PIL import Image
        events = [
            {
                "type": "mouse",
                "action": "move",
                "delay_ms": 12,
                "pos": [0.50, 0.50],
                "positions": [[0.50, 0.50], [0.51, 0.51], [0.52, 0.52]],
                "delays": [12, 15],
            },
        ]
        mock_grab.return_value = Image.new("RGB", (1920, 1080))
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir, events)
            player = Player(tmpdir, use_match=False)
            player._start_stop_listener = MagicMock()
            player._stop_listener = MagicMock()
            player._check_stop = MagicMock(return_value=False)
            player._stop_flag = False

            player.play()

            assert mock_setcursor.call_count == 3
            sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
            assert 0.012 in sleep_calls
            assert 0.015 in sleep_calls

    @patch("engine.player.win32api.SetCursorPos")
    @patch("engine.player.time.sleep")
    @patch("engine.player.ImageGrab.grab")
    def test_legacy_event_no_positions_still_works(self, mock_grab, mock_sleep, mock_setcursor):
        from PIL import Image
        events = [
            {
                "type": "mouse",
                "action": "move",
                "delay_ms": 500,
                "pos": [0.5, 0.5],
            },
        ]
        mock_grab.return_value = Image.new("RGB", (1920, 1080))
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir, events)
            player = Player(tmpdir, use_match=False)
            player._start_stop_listener = MagicMock()
            player._stop_listener = MagicMock()
            player._check_stop = MagicMock(return_value=False)
            player._stop_flag = False

            player.play()

            assert mock_setcursor.call_count == 1
            assert mock_setcursor.call_args_list[0] == call((960, 540),)


class TestPlayerPause:
    def _make_script_dir(self, tmpdir):
        data = {
            "version": 1,
            "meta": {
                "created": "2026-08-14T10:00:00",
                "screen": [1920, 1080],
                "duration_ms": 100,
                "event_count": 1,
            },
            "events": [
                {
                    "type": "mouse",
                    "action": "move",
                    "delay_ms": 100,
                    "pos": [0.5, 0.5],
                },
            ],
        }
        script_path = os.path.join(tmpdir, "script.json")
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return tmpdir

    def test_check_pause_false_when_hooks_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, use_match=False)
            assert player._check_pause() is False

    def test_check_pause_false_when_flag_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, use_match=False)
            hooks = MagicMock()
            hooks.pause_flag = False
            player._hooks = hooks
            assert player._check_pause() is False

    def test_check_pause_true_when_flag_true(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, use_match=False)
            hooks = MagicMock()
            hooks.pause_flag = True
            player._hooks = hooks
            assert player._check_pause() is True

    def test_log_event_progress_format(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, use_match=False)
            player._log_event_progress(5, 230, "mouse", "left_down", "pos=[0.32,0.45]", "shot=shots/0001.png")
            captured = capsys.readouterr()
            assert "[PLAY]" in captured.out
            assert "Event 5/230" in captured.out
            assert "mouse" in captured.out
            assert "left_down" in captured.out
            assert "pos=[0.32,0.45]" in captured.out
            assert "shot=shots/0001.png" in captured.out

    def test_log_event_progress_no_details(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_script_dir(tmpdir)
            player = Player(tmpdir, use_match=False)
            player._log_event_progress(0, 10, "key", "a down", "keycode=65")
            captured = capsys.readouterr()
            assert "[PLAY] Event 0/10 key a down keycode=65" in captured.out