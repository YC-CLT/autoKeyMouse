from unittest.mock import patch

from config import DRAG_THRESHOLD_MS
from engine.recorder import Recorder


class TestRecorderDrag:
    @patch("time.time")
    def test_drag_moves_not_throttled(self, mock_time):
        mock_time.side_effect = [1000.0, 1000.4, 1000.45, 1000.5]
        recorder = Recorder("/tmp/test", no_shot=True)
        recorder._screen_w = 1920
        recorder._screen_h = 1080
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0

        recorder._on_mouse_callback({
            "action": "left_down",
            "pos": [100, 200],
            "wheel": 0,
            "timestamp": 1000.0,
        })
        assert recorder._drag_button == "left"
        assert recorder._drag_move_count == 0

        recorder._on_mouse_callback({
            "action": "move",
            "pos": [150, 250],
            "wheel": 0,
            "timestamp": 1000.4,
        })
        recorder._on_mouse_callback({
            "action": "move",
            "pos": [200, 300],
            "wheel": 0,
            "timestamp": 1000.45,
        })
        recorder._on_mouse_callback({
            "action": "move",
            "pos": [250, 350],
            "wheel": 0,
            "timestamp": 1000.5,
        })

        assert recorder._drag_move_count == 3
        recorder._flush_move_buffer()
        move_events = [e for e in recorder._events if e.action == "move"]
        assert len(move_events) == 1
        compressed = move_events[0]
        assert len(compressed.positions) == 3
        assert len(compressed.delays) == 2

    @patch("time.time")
    def test_click_moves_throttled(self, mock_time):
        mock_time.side_effect = [1000.0, 1000.1, 1000.3]
        recorder = Recorder("/tmp/test", record_move=True, move_interval=200)
        recorder._screen_w = 1920
        recorder._screen_h = 1080
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0
        recorder._last_mouse_move_time = 999.0

        recorder._on_mouse_callback({
            "action": "move",
            "pos": [100, 200],
            "wheel": 0,
            "timestamp": 1000.0,
        })
        recorder._flush_move_buffer()
        assert len(recorder._events) == 1

        recorder._on_mouse_callback({
            "action": "move",
            "pos": [110, 210],
            "wheel": 0,
            "timestamp": 1000.1,
        })
        recorder._flush_move_buffer()
        assert len(recorder._events) == 1

        recorder._on_mouse_callback({
            "action": "move",
            "pos": [200, 300],
            "wheel": 0,
            "timestamp": 1000.3,
        })
        recorder._flush_move_buffer()
        assert len(recorder._events) == 2

    @patch("time.time")
    def test_drag_up_has_shot(self, mock_time):
        mock_time.side_effect = [1000.0, 1000.4, 1000.5]
        with patch("engine.recorder.capture", return_value="shots/shot_001.png") as mock_capture:
            recorder = Recorder("/tmp/test")
            recorder._screen_w = 1920
            recorder._screen_h = 1080
            recorder._start_time = 1000.0
            recorder._last_event_time = 1000.0

            recorder._on_mouse_callback({
                "action": "left_down",
                "pos": [100, 200],
                "wheel": 0,
                "timestamp": 1000.0,
            })
            recorder._on_mouse_callback({
                "action": "move",
                "pos": [150, 250],
                "wheel": 0,
                "timestamp": 1000.4,
            })
            recorder._on_mouse_callback({
                "action": "left_up",
                "pos": [200, 300],
                "wheel": 0,
                "timestamp": 1000.5,
            })

            up_event = recorder._events[-1]
            assert up_event.action == "left_up"
            assert up_event.shot is not None

    @patch("time.time")
    def test_click_up_no_shot(self, mock_time):
        mock_time.side_effect = [1000.0, 1000.05]
        with patch("engine.recorder.capture", return_value="shots/shot_000.png") as mock_capture:
            recorder = Recorder("/tmp/test")
            recorder._screen_w = 1920
            recorder._screen_h = 1080
            recorder._start_time = 1000.0
            recorder._last_event_time = 1000.0

            recorder._on_mouse_callback({
                "action": "left_down",
                "pos": [100, 200],
                "wheel": 0,
                "timestamp": 1000.0,
            })
            recorder._on_mouse_callback({
                "action": "left_up",
                "pos": [100, 200],
                "wheel": 0,
                "timestamp": 1000.05,
            })

            up_event = recorder._events[-1]
            assert up_event.action == "left_up"
            assert up_event.shot is None

    @patch("time.time")
    def test_short_drag_no_move_recorded(self, mock_time):
        mock_time.side_effect = [1000.0, 1000.1]
        recorder = Recorder("/tmp/test", no_shot=True)
        recorder._screen_w = 1920
        recorder._screen_h = 1080
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0

        recorder._on_mouse_callback({
            "action": "left_down",
            "pos": [100, 200],
            "wheel": 0,
            "timestamp": 1000.0,
        })

        recorder._on_mouse_callback({
            "action": "move",
            "pos": [110, 210],
            "wheel": 0,
            "timestamp": 1000.1,
        })

        move_events = [e for e in recorder._events if e.action == "move"]
        assert len(move_events) == 0
        assert recorder._drag_move_count == 0

    @patch("time.time")
    def test_drag_threshold_exact(self, mock_time):
        threshold_s = DRAG_THRESHOLD_MS / 1000.0
        mock_time.side_effect = [1000.0, 1000.0 + threshold_s]
        recorder = Recorder("/tmp/test", no_shot=True)
        recorder._screen_w = 1920
        recorder._screen_h = 1080
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0

        recorder._on_mouse_callback({
            "action": "left_down",
            "pos": [100, 200],
            "wheel": 0,
            "timestamp": 1000.0,
        })

        recorder._on_mouse_callback({
            "action": "move",
            "pos": [150, 250],
            "wheel": 0,
            "timestamp": 1000.0 + threshold_s,
        })

        recorder._flush_move_buffer()
        move_events = [e for e in recorder._events if e.action == "move"]
        assert len(move_events) == 1
        assert recorder._drag_move_count == 1

    @patch("time.time")
    def test_drag_button_cleared_on_up(self, mock_time):
        mock_time.side_effect = [1000.0, 1000.4, 1000.5]
        recorder = Recorder("/tmp/test", no_shot=True)
        recorder._screen_w = 1920
        recorder._screen_h = 1080
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0

        recorder._on_mouse_callback({
            "action": "left_down",
            "pos": [100, 200],
            "wheel": 0,
            "timestamp": 1000.0,
        })
        assert recorder._drag_button == "left"

        recorder._on_mouse_callback({
            "action": "move",
            "pos": [150, 250],
            "wheel": 0,
            "timestamp": 1000.4,
        })
        recorder._on_mouse_callback({
            "action": "left_up",
            "pos": [200, 300],
            "wheel": 0,
            "timestamp": 1000.5,
        })

        assert recorder._drag_button is None
        assert recorder._drag_start_time == 0.0