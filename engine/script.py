import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Event:
    type: str
    action: str
    delay_ms: int
    pos: Optional[list[float]] = None
    key: Optional[str] = None
    keycode: Optional[int] = None
    text: Optional[str] = None
    shot: Optional[str] = None
    positions: Optional[list[list[float]]] = None
    delays: Optional[list[int]] = None


@dataclass
class Meta:
    created: str = ""
    screen: list[int] = field(default_factory=lambda: [0, 0])
    duration_ms: int = 0
    event_count: int = 0


@dataclass
class Script:
    version: int = 1
    meta: Meta = field(default_factory=Meta)
    events: list[Event] = field(default_factory=list)


def load(dir_path: str) -> Script:
    script_path = os.path.join(dir_path, "script.json")
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"script.json not found in {dir_path}")

    with open(script_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta_data = data.get("meta", {})
    meta = Meta(
        created=meta_data.get("created", ""),
        screen=meta_data.get("screen", [0, 0]),
        duration_ms=meta_data.get("duration_ms", 0),
        event_count=meta_data.get("event_count", 0),
    )

    events = []
    for ev_data in data.get("events", []):
        e = Event(
            type=ev_data["type"],
            action=ev_data["action"],
            delay_ms=ev_data["delay_ms"],
            pos=ev_data.get("pos"),
            key=ev_data.get("key"),
            keycode=ev_data.get("keycode"),
            text=ev_data.get("text"),
            shot=ev_data.get("shot"),
        )
        events.append(e)

    return Script(version=data.get("version", 1), meta=meta, events=events)


def save(script: Script, dir_path: str) -> None:
    os.makedirs(dir_path, exist_ok=True)

    data = {
        "version": script.version,
        "meta": {
            "created": script.meta.created,
            "screen": script.meta.screen,
            "duration_ms": script.meta.duration_ms,
            "event_count": script.meta.event_count,
        },
        "events": [
            {
                "type": e.type,
                "action": e.action,
                "delay_ms": e.delay_ms,
                "pos": e.pos,
                "key": e.key,
                "keycode": e.keycode,
                "text": e.text,
                "shot": e.shot,
            }
            for e in script.events
        ],
    }

    script_path = os.path.join(dir_path, "script.json")
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def validate(script: Script, base_dir: str = "") -> list[str]:
    errors = []

    if script.meta.event_count != len(script.events):
        errors.append(
            f"event_count mismatch: meta.event_count={script.meta.event_count}, "
            f"actual events={len(script.events)}"
        )

    key_states: dict[str, list[int]] = {}
    for i, e in enumerate(script.events):
        if e.type == "key":
            key_name = e.key or f"keycode_{e.keycode}"
            if key_name not in key_states:
                key_states[key_name] = []
            key_states[key_name].append(i)

    for key_name, indices in key_states.items():
        if len(indices) % 2 != 0:
            errors.append(f"key '{key_name}' has unpaired down/up events (count={len(indices)})")

    for i, e in enumerate(script.events):
        if e.type == "mouse" and e.pos is None:
            errors.append(f"mouse event at index {i} missing pos")

    if base_dir:
        for i, e in enumerate(script.events):
            if e.shot:
                shot_path = os.path.join(base_dir, e.shot)
                if not os.path.exists(shot_path):
                    errors.append(f"shot file not found: {e.shot} (event {i})")

    return errors