import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from engine.recorder import Recorder


class TestRecorder:
    def test_directory_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "test_script")
            recorder = Recorder(output_dir)
            recorder._build_output_dir()
            assert os.path.isdir(output_dir)
            assert os.path.isdir(os.path.join(output_dir, "shots"))

    def test_build_key_event(self):
        recorder = Recorder("/tmp/test")
        mock_hook_event = MagicMock()
        mock_hook_event.MessageName = "key down"
        mock_hook_event.Key = "A"
        mock_hook_event.KeyID = 65
        mock_hook_event.Ascii = 97

        event = recorder._build_key_event(mock_hook_event, delay_ms=50)
        assert event.type == "key"
        assert event.action == "down"
        assert event.key == "A"
        assert event.keycode == 65
        assert event.delay_ms == 50

    def test_build_key_up_event(self):
        recorder = Recorder("/tmp/test")
        mock_hook_event = MagicMock()
        mock_hook_event.MessageName = "key up"
        mock_hook_event.Key = "Shift"
        mock_hook_event.KeyID = 160
        mock_hook_event.Ascii = 0

        event = recorder._build_key_event(mock_hook_event, delay_ms=100)
        assert event.type == "key"
        assert event.action == "up"
        assert event.key == "Shift"
        assert event.keycode == 160
        assert event.delay_ms == 100

    def test_build_mouse_click_event(self):
        recorder = Recorder("/tmp/test")
        recorder._shot_index = 2
        mock_hook_event = MagicMock()
        mock_hook_event.MessageName = "mouse left down"
        mock_hook_event.Position = (100, 200)

        with patch.object(recorder, "_last_shot", None):
            event = recorder._build_mouse_event(mock_hook_event, delay_ms=30)
            assert event.type == "mouse"
            assert event.action == "click"
            assert event.pos == [100, 200]
            assert event.delay_ms == 30
            assert event.shot is not None

    def test_build_mouse_right_click_event(self):
        recorder = Recorder("/tmp/test")
        mock_hook_event = MagicMock()
        mock_hook_event.MessageName = "mouse right down"
        mock_hook_event.Position = (300, 400)

        with patch.object(recorder, "_last_shot", None):
            event = recorder._build_mouse_event(mock_hook_event, delay_ms=20)
            assert event.type == "mouse"
            assert event.action == "rightclick"
            assert event.pos == [300, 400]
            assert event.delay_ms == 20

    def test_shot_index_increments(self):
        recorder = Recorder("/tmp/test")
        assert recorder._shot_index == 0
        mock_hook_event = MagicMock()
        mock_hook_event.MessageName = "mouse left down"
        mock_hook_event.Position = (100, 200)

        with patch.object(recorder, "_last_shot", None):
            recorder._build_mouse_event(mock_hook_event, delay_ms=10)
            assert recorder._shot_index == 1
            recorder._build_mouse_event(mock_hook_event, delay_ms=10)
            assert recorder._shot_index == 2

    def test_build_script_metadata(self):
        recorder = Recorder("/tmp/test")
        recorder._events = []
        recorder._start_time = 1000.0
        recorder._last_event_time = 1004.0

        script = recorder._build_script()
        assert script.version == 1
        assert abs(script.meta.duration_ms - 4000) <= 1
        assert script.meta.event_count == 0

    def test_script_includes_events(self):
        recorder = Recorder("/tmp/test")
        from engine.script import Event

        recorder._events = [
            Event(type="key", action="down", delay_ms=10, key="A", keycode=65),
            Event(type="key", action="up", delay_ms=20, key="A", keycode=65),
        ]
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.03

        script = recorder._build_script()
        assert script.meta.event_count == 2
        assert len(script.events) == 2
        assert abs(script.meta.duration_ms - 30) <= 1