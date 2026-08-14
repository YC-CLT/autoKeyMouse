import json
import os
import tempfile
from pathlib import Path

import pytest

from engine.script import Event, Meta, Script, load, save, validate


class TestEvent:
    def test_event_creation_minimal(self):
        e = Event(type="key", action="down", delay_ms=100, key="a", keycode=65)
        assert e.type == "key"
        assert e.action == "down"
        assert e.delay_ms == 100
        assert e.key == "a"
        assert e.keycode == 65
        assert e.pos is None
        assert e.text is None
        assert e.shot is None

    def test_event_creation_mouse(self):
        e = Event(type="mouse", action="left_down", delay_ms=50, pos=[0.5, 0.5], shot="shots/0001.png")
        assert e.type == "mouse"
        assert e.pos == [0.5, 0.5]
        assert e.shot == "shots/0001.png"

    def test_event_creation_text(self):
        e = Event(type="text", action="input", delay_ms=100, text="hello")
        assert e.text == "hello"


class TestScript:
    def test_script_defaults(self):
        s = Script()
        assert s.version == 1
        assert s.meta == Meta()
        assert s.events == []

    def test_script_with_events(self):
        events = [
            Event(type="key", action="down", delay_ms=100, key="a", keycode=65),
            Event(type="key", action="up", delay_ms=50, key="a", keycode=65),
        ]
        meta = Meta(created="2026-08-12T14:30:00", screen=[1920, 1080], duration_ms=150, event_count=2)
        s = Script(version=1, meta=meta, events=events)
        assert len(s.events) == 2
        assert s.meta.event_count == 2


class TestSaveLoad:
    def test_roundtrip(self):
        events = [
            Event(type="key", action="down", delay_ms=100, key="a", keycode=65),
            Event(type="key", action="up", delay_ms=50, key="a", keycode=65),
        ]
        meta = Meta(created="2026-08-12T14:30:00", screen=[1920, 1080], duration_ms=150, event_count=2)
        s = Script(version=1, meta=meta, events=events)

        with tempfile.TemporaryDirectory() as tmpdir:
            save(s, tmpdir)
            loaded = load(tmpdir)

            assert loaded.version == s.version
            assert loaded.meta.created == s.meta.created
            assert loaded.meta.screen == s.meta.screen
            assert loaded.meta.duration_ms == s.meta.duration_ms
            assert loaded.meta.event_count == s.meta.event_count
            assert len(loaded.events) == len(s.events)
            for orig, loaded_ev in zip(s.events, loaded.events):
                assert loaded_ev.type == orig.type
                assert loaded_ev.action == orig.action
                assert loaded_ev.delay_ms == orig.delay_ms
                assert loaded_ev.key == orig.key
                assert loaded_ev.keycode == orig.keycode
                assert loaded_ev.pos == orig.pos
                assert loaded_ev.text == orig.text
                assert loaded_ev.shot == orig.shot

    def test_load_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                load(tmpdir)

    def test_save_creates_file(self):
        s = Script(meta=Meta(created="2026-08-12T14:30:00", screen=[1920, 1080], duration_ms=0, event_count=0))
        with tempfile.TemporaryDirectory() as tmpdir:
            save(s, tmpdir)
            assert os.path.exists(os.path.join(tmpdir, "script.json"))

    def test_roundtrip_with_positions(self):
        events = [
            Event(type="mouse", action="move", delay_ms=534, pos=[0.53, 0.88],
                  positions=[[0.53, 0.88], [0.54, 0.88], [0.55, 0.88]],
                  delays=None),
            Event(type="mouse", action="left_down", delay_ms=100, pos=[0.60, 0.60], shot="shots/0001.png"),
            Event(type="mouse", action="move", delay_ms=12, pos=[0.50, 0.50],
                  positions=[[0.50, 0.50], [0.51, 0.51], [0.52, 0.52]],
                  delays=[12, 15]),
            Event(type="mouse", action="left_up", delay_ms=50, pos=[0.52, 0.52]),
        ]
        meta = Meta(created="2026-08-14T10:00:00", screen=[1920, 1080], duration_ms=696, event_count=4)
        s = Script(meta=meta, events=events)

        with tempfile.TemporaryDirectory() as tmpdir:
            save(s, tmpdir)
            loaded = load(tmpdir)
            assert loaded.events[0].positions == [[0.53, 0.88], [0.54, 0.88], [0.55, 0.88]]
            assert loaded.events[0].delays is None
            assert loaded.events[2].positions == [[0.50, 0.50], [0.51, 0.51], [0.52, 0.52]]
            assert loaded.events[2].delays == [12, 15]

    def test_roundtrip_without_positions(self):
        data = {
            "version": 1,
            "meta": {"created": "2026-08-14T10:00:00", "screen": [1920, 1080], "duration_ms": 100, "event_count": 1},
            "events": [{"type": "mouse", "action": "move", "delay_ms": 534, "pos": [0.53, 0.88]}],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "script.json")
            with open(script_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            loaded = load(tmpdir)
            assert loaded.events[0].positions is None
            assert loaded.events[0].delays is None


class TestValidate:
    def test_valid_script_no_errors(self):
        events = [
            Event(type="key", action="down", delay_ms=100, key="a", keycode=65),
            Event(type="key", action="up", delay_ms=50, key="a", keycode=65),
        ]
        meta = Meta(created="2026-08-12T14:30:00", screen=[1920, 1080], duration_ms=150, event_count=2)
        s = Script(meta=meta, events=events)
        errors = validate(s)
        assert errors == []

    def test_event_count_mismatch(self):
        events = [
            Event(type="key", action="down", delay_ms=100, key="a", keycode=65),
        ]
        meta = Meta(created="2026-08-12T14:30:00", screen=[1920, 1080], duration_ms=100, event_count=999)
        s = Script(meta=meta, events=events)
        errors = validate(s)
        assert any("event_count" in err.lower() for err in errors)

    def test_key_unpaired(self):
        events = [
            Event(type="key", action="down", delay_ms=100, key="a", keycode=65),
        ]
        meta = Meta(created="2026-08-12T14:30:00", screen=[1920, 1080], duration_ms=100, event_count=1)
        s = Script(meta=meta, events=events)
        errors = validate(s)
        assert any("unpaired" in err.lower() or "不成对" in err.lower() for err in errors)

    def test_key_paired_correctly(self):
        events = [
            Event(type="key", action="down", delay_ms=100, key="a", keycode=65),
            Event(type="key", action="up", delay_ms=50, key="a", keycode=65),
            Event(type="key", action="down", delay_ms=100, key="ctrl", keycode=162),
            Event(type="key", action="down", delay_ms=80, key="c", keycode=67),
            Event(type="key", action="up", delay_ms=50, key="c", keycode=67),
            Event(type="key", action="up", delay_ms=120, key="ctrl", keycode=162),
        ]
        meta = Meta(created="2026-08-12T14:30:00", screen=[1920, 1080], duration_ms=500, event_count=6)
        s = Script(meta=meta, events=events)
        errors = validate(s)
        assert not any("unpaired" in err.lower() or "不成对" in err.lower() for err in errors)

    def test_mouse_missing_pos(self):
        events = [
            Event(type="mouse", action="left_down", delay_ms=100, pos=None),
        ]
        meta = Meta(created="2026-08-12T14:30:00", screen=[1920, 1080], duration_ms=100, event_count=1)
        s = Script(meta=meta, events=events)
        errors = validate(s)
        assert any("pos" in err.lower() for err in errors)

    def test_shot_file_missing(self):
        events = [
            Event(type="mouse", action="left_down", delay_ms=100, pos=[0.5, 0.5], shot="shots/nonexistent.png"),
        ]
        meta = Meta(created="2026-08-12T14:30:00", screen=[1920, 1080], duration_ms=100, event_count=1)
        s = Script(meta=meta, events=events)
        with tempfile.TemporaryDirectory() as tmpdir:
            errors = validate(s, base_dir=tmpdir)
            assert any("shot" in err.lower() for err in errors)

    def test_shot_file_exists(self):
        events = [
            Event(type="mouse", action="left_down", delay_ms=100, pos=[0.5, 0.5], shot="shots/0001.png"),
        ]
        meta = Meta(created="2026-08-12T14:30:00", screen=[1920, 1080], duration_ms=100, event_count=1)
        s = Script(meta=meta, events=events)
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "shots"), exist_ok=True)
            Path(os.path.join(tmpdir, "shots", "0001.png")).touch()
            errors = validate(s, base_dir=tmpdir)
            shot_errors = [e for e in errors if "shot" in e.lower()]
            assert len(shot_errors) == 0