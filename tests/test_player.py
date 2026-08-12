import json
import os
import tempfile
from unittest.mock import MagicMock, PropertyMock, patch

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
            assert player._use_match is True
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
            x, y = player._pos_match(event, None, 1920, 1080)
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
            x, y = player._pos_match(event, None, 1920, 1080)
            assert x == 960
            assert y == 540

    def test_pos_match_with_kalman_and_mock_matcher(self):
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

            mock_kalman = MagicMock()
            mock_kalman.predict.return_value = (950.0, 540.0)
            type(mock_kalman).position = PropertyMock(return_value=(955.0, 545.0))

            dummy_shot = np.zeros((50, 50), dtype=np.float64)
            dummy_screen = np.zeros((200, 200), dtype=np.float64)

            with patch.object(player, "_load_shot", return_value=dummy_shot), \
                 patch.object(player, "_capture_screen", return_value=dummy_screen), \
                 patch("engine.player.match_template", return_value=((955, 545), 0.95)):
                event = player._script.events[0]
                x, y = player._pos_match(event, mock_kalman, 1920, 1080)
                mock_kalman.predict.assert_called_once()
                mock_kalman.update.assert_called_once()
                call_args = mock_kalman.update.call_args[0][0]
                assert call_args[0] == 955.0
                assert call_args[1] == 545.0
                assert x == 955
                assert y == 545

    def test_pos_match_fallback_to_kalman_on_match_failure(self):
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

            mock_kalman = MagicMock()
            mock_kalman.predict.return_value = (950.0, 540.0)

            dummy_shot = np.zeros((50, 50), dtype=np.float64)
            dummy_screen = np.zeros((200, 200), dtype=np.float64)

            with patch.object(player, "_load_shot", return_value=dummy_shot), \
                 patch.object(player, "_capture_screen", return_value=dummy_screen), \
                 patch("engine.player.match_template", return_value=None):
                event = player._script.events[0]
                x, y = player._pos_match(event, mock_kalman, 1920, 1080)
                mock_kalman.predict.assert_called_once()
                mock_kalman.update.assert_not_called()
                assert x == 950
                assert y == 540