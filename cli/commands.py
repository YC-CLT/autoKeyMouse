import argparse
import os
import time
from datetime import datetime

from cli.display import (
    print_playback_done,
    print_playback_start,
    print_recording_done,
    print_recording_start,
    print_script_list,
    print_summary,
)
from engine.player import Player
from engine.recorder import Recorder
from engine.script import Event, Script, load, save
from engine.logger import get_logger
from config import SHOT_RADIUS, MOUSE_MOVE_INTERVAL_MS

_log = get_logger("cli.commands")


def register_commands(subparsers) -> None:
    record_parser = subparsers.add_parser("record", help="Start recording")
    record_parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output directory (default: scripts/<timestamp>/)",
    )
    record_parser.add_argument(
        "--no-record-move", action="store_false", dest="record_move", default=True,
        help="Disable recording mouse movement",
    )
    record_parser.add_argument(
        "--move-interval", type=int, default=MOUSE_MOVE_INTERVAL_MS,
        help=f"Minimum interval between mouse move events in ms (default: {MOUSE_MOVE_INTERVAL_MS})",
    )
    record_parser.add_argument(
        "--shot-radius", type=int, default=SHOT_RADIUS,
        help=f"Screenshot crop radius in pixels (default: {SHOT_RADIUS})",
    )
    record_parser.add_argument(
        "--no-shot", action="store_true", default=False,
        help="Disable screenshots for mouse events",
    )
    record_parser.add_argument(
        "--no-compress", action="store_true", default=False,
        help="Disable move compression (keep all move events individually)",
    )

    play_parser = subparsers.add_parser("play", help="Play back a recorded script")
    play_parser.add_argument("script", type=str, help="Script directory to play")
    play_parser.add_argument(
        "--times", "-n", type=int, default=1,
        help="Number of times to repeat (default: 1)",
    )
    play_parser.add_argument(
        "--speed", "-s", type=float, default=1.0,
        help="Playback speed multiplier (default: 1.0)",
    )
    play_parser.add_argument(
        "--match", action="store_true", default=False,
        help="[EXPERIMENTAL] Enable template matching (unreliable, for debugging only)",
    )

    list_parser = subparsers.add_parser("list", help="List recorded scripts")
    list_parser.add_argument(
        "dir", type=str, nargs="?", default=None,
        help="Directory to list scripts from (default: scripts/)",
    )

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a script file")
    inspect_parser.add_argument("script", type=str, help="Script directory to inspect")

    tui_parser = subparsers.add_parser("tui", help="Launch interactive TUI")


def _default_output_dir() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    return os.path.join("scripts", timestamp)


def handle_record(args) -> int:
    output_dir = args.output or _default_output_dir()
    _log.info("Command: record output=%s record_move=%s", output_dir, args.record_move)

    recorder = Recorder(
        output_dir=output_dir,
        record_move=args.record_move,
        move_interval=args.move_interval,
        shot_radius=args.shot_radius,
        no_shot=args.no_shot,
        compress=not args.no_compress,
    )

    print_recording_start()
    recorder.start()

    try:
        while recorder.is_recording():
            if recorder._hooks is not None and recorder._hooks.stop_flag:
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    script = recorder.stop()
    save(script, output_dir)
    print_recording_done(script)
    return 0


def handle_play(args) -> int:
    script_dir = args.script
    _log.info("Command: play script=%s times=%d speed=%.1f match=%s",
              script_dir, args.times, args.speed, args.match)

    if args.match:
        from rich.console import Console
        Console().print(
            "[bold yellow]WARNING:[/bold yellow] Template matching is [bold red]EXPERIMENTAL[/bold red] and unreliable. "
            "Use at your own risk.",
        )

    print_playback_start(script_dir, args.times)

    player = Player(
        script_dir=script_dir,
        times=args.times,
        speed=args.speed,
        use_match=args.match,
    )

    result = player.play()
    print_playback_done(result)
    return 0


def handle_list(args) -> int:
    base_dir = args.dir or "scripts"
    _log.info("Command: list dir=%s", base_dir)
    scripts = []

    if os.path.isdir(base_dir):
        for name in sorted(os.listdir(base_dir)):
            script_path = os.path.join(base_dir, name, "script.json")
            if os.path.isfile(script_path):
                try:
                    script = load(os.path.join(base_dir, name))
                    scripts.append({
                        "name": name,
                        "created": script.meta.created,
                        "event_count": script.meta.event_count,
                        "duration_ms": script.meta.duration_ms,
                    })
                except Exception:
                    pass

    print_script_list(scripts)
    return 0


def handle_inspect(args) -> int:
    _log.info("Command: inspect script=%s", args.script)
    try:
        script = load(args.script)
        print_summary(script)
        return 0
    except Exception as e:
        _log.error("Failed to load script: %s error=%s", args.script, e)
        raise