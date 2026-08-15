from engine.script import Event, Script


def print_summary(script: Script) -> None:
    print(f"[SCRIPT] created={script.meta.created} "
          f"screen={script.meta.screen[0]}x{script.meta.screen[1]} "
          f"duration={script.meta.duration_ms}ms "
          f"events={script.meta.event_count}")


def print_event_list(events: list[Event]) -> None:
    for i, event in enumerate(events):
        details = _event_details(event)
        print(f"[EVENT] {i} {event.type} {event.action} "
              f"delay={event.delay_ms}ms {details}")


def _event_details(event: Event) -> str:
    if event.type == "key":
        return f"key={event.key} keycode={event.keycode}"
    elif event.type == "text":
        return f"text={event.text}"
    elif event.type == "mouse":
        if event.action == "move":
            if event.positions is not None:
                n = len(event.positions)
                drag = " drag=yes" if event.delays is not None else ""
                return f"pos={event.positions[0]} compressed={n}{drag}"
            return f"pos={event.pos}"
        parts = [f"pos={event.pos}"]
        if event.shot:
            parts.append(f"shot={event.shot}")
        return " ".join(parts)
    return ""


def print_recording_start() -> None:
    print("[RECORD] Started (F9 to stop)")


def print_recording_done(script: Script, output_dir: str) -> None:
    print(f"[RECORD] Done events={script.meta.event_count} "
          f"duration={script.meta.duration_ms}ms "
          f"saved={output_dir}")


def print_playback_start(script_name: str, times: int, speed: float = 1.0) -> None:
    print(f"[PLAY] script={script_name} times={times} speed={speed}")


def print_playback_done(result) -> None:
    status = "stopped" if result.stopped_early else "completed"
    print(f"[PLAY] Done cycles={result.completed_cycles} "
          f"time={result.total_time_ms}ms status={status}")


def print_script_list(scripts: list[dict]) -> None:
    for s in scripts:
        print(f"[SCRIPT] name={s.get('name', '')} "
              f"created={s.get('created', '')} "
              f"events={s.get('event_count', 0)} "
              f"duration={s.get('duration_ms', 0)}ms")