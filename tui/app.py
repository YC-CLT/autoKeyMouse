import msvcrt
import os
import time
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from cli.display import (
    print_event_list,
    print_playback_done,
    print_playback_start,
    print_recording_done,
    print_recording_start,
    print_script_list,
    print_summary,
)
from engine.logger import setup_logging, get_logger
from engine.player import Player
from engine.recorder import Recorder
from engine.script import load, save
from config import SHOT_RADIUS, MOUSE_MOVE_INTERVAL_MS

_log = get_logger("tui.app")

console = Console()


def _show_menu() -> str:
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]autokeymouse[/bold cyan] - Keyboard/Mouse Recorder & Player",
        subtitle="TUI Mode",
    ))

    table = Table(show_header=False, box=None)
    table.add_column("Key", style="bold cyan", justify="right")
    table.add_column("Action", style="white")
    table.add_row("[1]", "Record new script")
    table.add_row("[2]", "Play a script")
    table.add_row("[3]", "List scripts")
    table.add_row("[4]", "Inspect a script")
    table.add_row("[q]", "Quit")
    console.print(table)

    choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "q"])
    return choice


def _default_output_dir() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    return os.path.join("scripts", timestamp)


def _tui_record() -> None:
    console.clear()
    console.print(Panel.fit("[bold]Record New Script[/bold]", title="Record"))

    use_default = Prompt.ask("Use default directory?", choices=["y", "n"], default="y")
    if use_default == "y":
        output_dir = _default_output_dir()
    else:
        output_dir = Prompt.ask("Output directory", default=_default_output_dir())

    no_shot = Prompt.ask("Disable screenshots?", choices=["y", "n"], default="n")
    shot_radius = 0 if no_shot == "y" else SHOT_RADIUS

    compress = Prompt.ask("Compress move events?", choices=["y", "n"], default="y")
    record_move = Prompt.ask("Record mouse movement?", choices=["y", "n"], default="y")
    move_interval = MOUSE_MOVE_INTERVAL_MS
    if record_move == "y":
        interval_str = Prompt.ask("Move interval (ms)", default=str(MOUSE_MOVE_INTERVAL_MS))
        try:
            move_interval = int(interval_str)
        except ValueError:
            move_interval = MOUSE_MOVE_INTERVAL_MS

    recorder = Recorder(
        output_dir=output_dir,
        shot_radius=shot_radius,
        record_move=record_move == "y",
        move_interval=move_interval,
        compress=compress == "y",
    )

    _log.info("TUI record: output=%s", output_dir)
    print_recording_start()
    console.print("[dim]Press Enter or F9 to stop recording...[/dim]")
    recorder.start()

    while True:
        if recorder._hooks is not None and recorder._hooks.stop_flag:
            break
        if msvcrt.kbhit():
            if msvcrt.getch() in (b'\r', b'\n'):
                break
        time.sleep(0.05)

    script = recorder.stop()
    save(script, output_dir)
    print_recording_done(script)
    input("\nPress Enter to return to menu...")


def _tui_play() -> None:
    console.clear()
    console.print(Panel.fit("[bold]Play Script[/bold]", title="Play"))

    scripts = _list_available_scripts()
    if not scripts:
        console.print("[yellow]No scripts found in scripts/[/yellow]")
        input("\nPress Enter to return to menu...")
        return

    print_script_list(scripts)
    script_name = Prompt.ask("Enter script name to play")

    script_dir = os.path.join("scripts", script_name)
    if not os.path.isdir(script_dir):
        console.print(f"[red]Script not found: {script_name}[/red]")
        input("\nPress Enter to return to menu...")
        return

    times_str = Prompt.ask("Repeat count", default="1")
    times = int(times_str) if times_str.isdigit() else 1

    speed_str = Prompt.ask("Speed multiplier", default="1.0")
    try:
        speed = float(speed_str)
    except ValueError:
        speed = 1.0

    use_match = Prompt.ask("Use template matching? [EXPERIMENTAL]", choices=["y", "n"], default="n")

    _log.info("TUI play: script=%s", script_dir)
    print_playback_start(script_name, times)
    player = Player(
        script_dir=script_dir,
        times=times,
        speed=speed,
        use_match=use_match == "y",
    )

    result = player.play()
    print_playback_done(result)
    input("\nPress Enter to return to menu...")


def _list_available_scripts() -> list[dict]:
    base_dir = "scripts"
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

    return scripts


def _tui_list() -> None:
    console.clear()
    scripts = _list_available_scripts()
    if not scripts:
        console.print("[yellow]No scripts found in scripts/[/yellow]")
    else:
        print_script_list(scripts)
    input("\nPress Enter to return to menu...")


def _tui_inspect() -> None:
    console.clear()
    console.print(Panel.fit("[bold]Inspect Script[/bold]", title="Inspect"))

    scripts = _list_available_scripts()
    if not scripts:
        console.print("[yellow]No scripts found in scripts/[/yellow]")
        input("\nPress Enter to return to menu...")
        return

    print_script_list(scripts)
    script_name = Prompt.ask("Enter script name to inspect")

    script_dir = os.path.join("scripts", script_name)
    if not os.path.isdir(script_dir):
        console.print(f"[red]Script not found: {script_name}[/red]")
        input("\nPress Enter to return to menu...")
        return

    try:
        script = load(script_dir)
        print_summary(script)
        print_event_list(script.events)
    except Exception as e:
        console.print(f"[red]Error loading script: {e}[/red]")

    input("\nPress Enter to return to menu...")


def run_tui() -> None:
    setup_logging()
    while True:
        choice = _show_menu()
        if choice == "1":
            _tui_record()
        elif choice == "2":
            _tui_play()
        elif choice == "3":
            _tui_list()
        elif choice == "4":
            _tui_inspect()
        elif choice == "q":
            console.print("[cyan]Goodbye![/cyan]")
            break