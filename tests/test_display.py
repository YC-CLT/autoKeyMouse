import pytest

from cli.display import (
    _event_details,
    print_event_list,
    print_playback_done,
    print_playback_start,
    print_recording_done,
    print_recording_start,
    print_script_list,
    print_summary,
)
from engine.script import Event, Meta, Script


class TestPrintSummary:
    def test_format(self, capsys):
        meta = Meta(
            created="2026-08-14 16:55:00",
            screen=[1920, 1080],
            duration_ms=12345,
            event_count=230,
        )
        script = Script(meta=meta, events=[])
        print_summary(script)
        captured = capsys.readouterr()
        assert "[SCRIPT]" in captured.out
        assert "created=2026-08-14 16:55:00" in captured.out
        assert "screen=1920x1080" in captured.out
        assert "duration=12345ms" in captured.out
        assert "events=230" in captured.out


class TestPrintEventList:
    def test_mouse_event(self, capsys):
        events = [
            Event(type="mouse", action="left_down", delay_ms=100, pos=[0.32, 0.45], shot="shots/0001.png"),
        ]
        print_event_list(events)
        captured = capsys.readouterr()
        assert "[EVENT] 0 mouse left_down" in captured.out
        assert "delay=100ms" in captured.out
        assert "pos=[0.32, 0.45]" in captured.out
        assert "shot=shots/0001.png" in captured.out

    def test_key_event(self, capsys):
        events = [
            Event(type="key", action="down", delay_ms=50, key="a", keycode=65),
        ]
        print_event_list(events)
        captured = capsys.readouterr()
        assert "[EVENT] 0 key down" in captured.out
        assert "key=a" in captured.out
        assert "keycode=65" in captured.out

    def test_text_event(self, capsys):
        events = [
            Event(type="text", action="input", delay_ms=200, text="hello"),
        ]
        print_event_list(events)
        captured = capsys.readouterr()
        assert "[EVENT] 0 text input" in captured.out
        assert "text=hello" in captured.out

    def test_compressed_move(self, capsys):
        events = [
            Event(type="mouse", action="move", delay_ms=500, pos=[0.1, 0.1],
                  positions=[[0.1, 0.1], [0.2, 0.2], [0.3, 0.3]], delays=None),
        ]
        print_event_list(events)
        captured = capsys.readouterr()
        assert "[EVENT] 0 mouse move" in captured.out
        assert "compressed=3" in captured.out

    def test_drag_move(self, capsys):
        events = [
            Event(type="mouse", action="move", delay_ms=12, pos=[0.5, 0.5],
                  positions=[[0.5, 0.5], [0.51, 0.51]], delays=[12]),
        ]
        print_event_list(events)
        captured = capsys.readouterr()
        assert "compressed=2" in captured.out
        assert "drag=yes" in captured.out


class TestPrintRecording:
    def test_recording_start(self, capsys):
        print_recording_start()
        captured = capsys.readouterr()
        assert "[RECORD] Started" in captured.out

    def test_recording_done(self, capsys):
        meta = Meta(
            created="2026-08-14 16:55:00",
            screen=[1920, 1080],
            duration_ms=12345,
            event_count=230,
        )
        script = Script(meta=meta, events=[])
        print_recording_done(script, "scripts/2026-08-14_1655")
        captured = capsys.readouterr()
        assert "[RECORD] Done" in captured.out
        assert "events=230" in captured.out
        assert "saved=scripts/2026-08-14_1655" in captured.out


class TestPrintPlayback:
    def test_playback_start(self, capsys):
        print_playback_start("2026-08-14_1655", 1, 1.0)
        captured = capsys.readouterr()
        assert "[PLAY] script=2026-08-14_1655" in captured.out
        assert "times=1" in captured.out
        assert "speed=1.0" in captured.out

    def test_playback_done(self, capsys):
        class FakeResult:
            completed_cycles = 3
            total_time_ms = 5000
            stopped_early = False

        print_playback_done(FakeResult)
        captured = capsys.readouterr()
        assert "[PLAY] Done" in captured.out
        assert "cycles=3" in captured.out
        assert "time=5000ms" in captured.out
        assert "status=completed" in captured.out


class TestPrintScriptList:
    def test_script_list(self, capsys):
        scripts = [
            {"name": "task1", "created": "2026-08-14 16:55:00", "event_count": 230, "duration_ms": 12345},
        ]
        print_script_list(scripts)
        captured = capsys.readouterr()
        assert "[SCRIPT] name=task1" in captured.out
        assert "created=2026-08-14 16:55:00" in captured.out
        assert "events=230" in captured.out
        assert "duration=12345ms" in captured.out