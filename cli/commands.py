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
from engine.script import Event, Script, load


def register_commands(subparsers) -> None:
    record_parser = subparsers.add_parser("record", help="Start recording")
    record_parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output directory (default: scripts/<timestamp>/)",
    )
    record_parser.add_argument(
        "--record-move", action="store_true", default=False,
        help="Record mouse movement",
    )
    record_parser.add_argument(
        "--move-interval", type=int, default=200,
        help="Minimum interval between mouse move events in ms (default: 200)",
    )
    record_parser.add_argument(
        "--shot-radius", type=int, default=50,
        help="Screenshot crop radius in pixels (default: 50)",
    )
    record_parser.add_argument(
        "--no-shot", action="store_true", default=False,
        help="Disable screenshots for mouse events",
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
        "--nomatch", action="store_true", default=False,
        help="Disable template matching and Kalman filtering",
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

    recorder = Recorder(output_dir=output_dir)

    print_recording_start()
    recorder.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    script = recorder.stop()
    print_recording_done(script)
    return 0


def handle_play(args) -> int:
    script_dir = args.script
    print_playback_start(script_dir, args.times)

    player = Player(
        script_dir=script_dir,
        times=args.times,
        speed=args.speed,
        use_match=not args.nomatch,
    )

    result = player.play()
    print_playback_done(result)
    return 0


def handle_list(args) -> int:
    base_dir = args.dir or "scripts"
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
    script = load(args.script)
    print_summary(script)
    return 0