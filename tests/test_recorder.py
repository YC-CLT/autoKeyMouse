import os
import tempfile
from unittest.mock import MagicMock, patch

from engine.recorder import Recorder
from engine.script import Event


class TestRecorder:
    def test_directory_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "test_script")
            recorder = Recorder(output_dir)
            recorder._build_output_dir()
            assert os.path.isdir(output_dir)
            assert os.path.isdir(os.path.join(output_dir, "shots"))

    def test_relative_pos(self):
        recorder = Recorder("/tmp/test")
        rx, ry = recorder._relative_pos(960.0, 540.0, 1920, 1080)
        assert rx == 0.5
        assert ry == 0.5

    def test_relative_pos_top_left(self):
        recorder = Recorder("/tmp/test")
        rx, ry = recorder._relative_pos(0.0, 0.0, 1920, 1080)
        assert rx == 0.0
        assert ry == 0.0

    def test_relative_pos_bottom_right(self):
        recorder = Recorder("/tmp/test")
        rx, ry = recorder._relative_pos(1920.0, 1080.0, 1920, 1080)
        assert rx == 1.0
        assert ry == 1.0

    def test_map_mouse_action_left_down(self):
        recorder = Recorder("/tmp/test")
        assert recorder._map_mouse_action("mouse left down") == "left_down"
        assert recorder._map_mouse_action("mouse left up") == "left_up"

    def test_map_mouse_action_right_down(self):
        recorder = Recorder("/tmp/test")
        assert recorder._map_mouse_action("mouse right down") == "right_down"
        assert recorder._map_mouse_action("mouse right up") == "right_up"

    def test_map_mouse_action_middle_down(self):
        recorder = Recorder("/tmp/test")
        assert recorder._map_mouse_action("mouse middle down") == "middle_down"
        assert recorder._map_mouse_action("mouse middle up") == "middle_up"

    def test_map_mouse_action_unknown(self):
        recorder = Recorder("/tmp/test")
        assert recorder._map_mouse_action("something else") is None

    def test_is_recording_initially_false(self):
        recorder = Recorder("/tmp/test")
        assert recorder.is_recording() is False

    def test_on_key_callback_creates_event(self):
        recorder = Recorder("/tmp/test")
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0
        recorder._on_key_callback({
            "key": "A",
            "keycode": 65,
            "action": "down",
            "timestamp": 1001.0,
        })
        assert len(recorder._events) == 1
        event = recorder._events[0]
        assert event.type == "key"
        assert event.action == "down"
        assert event.key == "A"
        assert event.keycode == 65

    def test_on_mouse_callback_creates_event(self):
        recorder = Recorder("/tmp/test")
        recorder._screen_w = 1920
        recorder._screen_h = 1080
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0
        recorder._on_mouse_callback({
            "action": "left_down",
            "pos": [960, 540],
            "wheel": 0,
            "timestamp": 1001.0,
        })
        assert len(recorder._events) == 1
        event = recorder._events[0]
        assert event.type == "mouse"
        assert event.action == "left_down"
        assert event.pos == [0.5, 0.5]

    def test_no_shot_skips_capture(self):
        recorder = Recorder("/tmp/test", no_shot=True)
        recorder._screen_w = 1920
        recorder._screen_h = 1080
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0
        recorder._on_mouse_callback({
            "action": "left_down",
            "pos": [100, 200],
            "wheel": 0,
            "timestamp": 1001.0,
        })
        event = recorder._events[0]
        assert event.shot is None

    def test_record_move_defaults_true(self):
        recorder = Recorder("/tmp/test")
        assert recorder._record_move is True

    def test_record_move_true(self):
        recorder = Recorder("/tmp/test", record_move=True)
        assert recorder._record_move is True

    def test_custom_shot_radius(self):
        recorder = Recorder("/tmp/test", shot_radius=80)
        assert recorder._shot_radius == 80

    def test_custom_move_interval(self):
        recorder = Recorder("/tmp/test", move_interval=500)
        assert recorder._move_interval == 500

    def test_build_script_metadata(self):
        recorder = Recorder("/tmp/test")
        recorder._screen_w = 1920
        recorder._screen_h = 1080
        recorder._events = []
        recorder._start_time = 1000.0
        recorder._last_event_time = 1004.0

        script = recorder._build_script()
        assert script.version == 1
        assert script.meta.screen == [1920, 1080]
        assert abs(script.meta.duration_ms - 4000) <= 1
        assert script.meta.event_count == 0

    def test_script_includes_events(self):
        recorder = Recorder("/tmp/test")
        recorder._screen_w = 1920
        recorder._screen_h = 1080
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

    def test_add_event_compresses_consecutive_moves(self):
        recorder = Recorder("/tmp/test", compress=True)
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0
        recorder._screen_w = 1920
        recorder._screen_h = 1080

        e1 = Event(type="mouse", action="move", delay_ms=500, pos=[0.1, 0.1])
        e2 = Event(type="mouse", action="move", delay_ms=200, pos=[0.2, 0.2])
        e3 = Event(type="mouse", action="move", delay_ms=200, pos=[0.3, 0.3])
        recorder._add_event(e1)
        recorder._add_event(e2)
        recorder._add_event(e3)
        assert len(recorder._events) == 0

        e4 = Event(type="mouse", action="left_down", delay_ms=100, pos=[0.3, 0.3])
        recorder._add_event(e4)
        assert len(recorder._events) == 2
        compressed = recorder._events[0]
        assert compressed.type == "mouse"
        assert compressed.action == "move"
        assert compressed.positions == [[0.1, 0.1], [0.2, 0.2], [0.3, 0.3]]
        assert compressed.delays is None
        assert compressed.pos == [0.1, 0.1]
        assert compressed.delay_ms == 500

    def test_add_event_single_move_not_compressed(self):
        recorder = Recorder("/tmp/test", compress=True)
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0

        e1 = Event(type="mouse", action="move", delay_ms=500, pos=[0.1, 0.1])
        recorder._add_event(e1)
        e2 = Event(type="key", action="down", delay_ms=100, key="a", keycode=65)
        recorder._add_event(e2)
        assert len(recorder._events) == 2
        assert recorder._events[0].positions is None

    def test_add_event_separates_normal_and_drag_moves(self):
        recorder = Recorder("/tmp/test", compress=True)
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0
        recorder._screen_w = 1920
        recorder._screen_h = 1080

        e1 = Event(type="mouse", action="move", delay_ms=500, pos=[0.1, 0.1])
        recorder._add_event(e1)

        recorder._drag_button = "left"
        recorder._move_is_drag = False

        e2 = Event(type="mouse", action="move", delay_ms=12, pos=[0.2, 0.2])
        recorder._add_event(e2)
        assert len(recorder._events) == 1
        assert len(recorder._move_buffer) == 1

    def test_no_compress_skips_buffer(self):
        recorder = Recorder("/tmp/test", compress=False)
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0

        e1 = Event(type="mouse", action="move", delay_ms=500, pos=[0.1, 0.1])
        e2 = Event(type="mouse", action="move", delay_ms=200, pos=[0.2, 0.2])
        recorder._add_event(e1)
        recorder._add_event(e2)
        assert len(recorder._events) == 2
        assert len(recorder._move_buffer) == 0

    def test_flush_move_buffer_on_stop(self):
        recorder = Recorder("/tmp/test", compress=True)
        recorder._start_time = 1000.0
        recorder._last_event_time = 1000.0
        recorder._screen_w = 1920
        recorder._screen_h = 1080

        e1 = Event(type="mouse", action="move", delay_ms=500, pos=[0.1, 0.1])
        recorder._add_event(e1)
        assert len(recorder._move_buffer) == 1
        assert len(recorder._events) == 0

        recorder._flush_move_buffer()
        assert len(recorder._move_buffer) == 0
        assert len(recorder._events) == 1
        assert recorder._events[0].positions is None