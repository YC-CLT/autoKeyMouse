from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from engine.script import Event, Script

console = Console()


def print_summary(script: Script) -> None:
    table = Table(title="Script Summary")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Created", script.meta.created)
    table.add_row("Screen", f"{script.meta.screen[0]}x{script.meta.screen[1]}")
    table.add_row("Duration", f"{script.meta.duration_ms}ms")
    table.add_row("Events", str(script.meta.event_count))

    console.print(table)


def print_event_list(events: list[Event]) -> None:
    table = Table(title="Event List")
    table.add_column("#", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Action", style="green")
    table.add_column("Delay (ms)", style="yellow")
    table.add_column("Details", style="white")

    for i, event in enumerate(events):
        details = ""
        if event.type == "key":
            details = f"key={event.key} keycode={event.keycode}"
        elif event.type == "mouse":
            details = f"pos={event.pos}"
            if event.shot:
                details += f" shot={event.shot}"
        elif event.type == "text":
            details = f"text={event.text}"

        table.add_row(
            str(i),
            event.type,
            event.action,
            str(event.delay_ms),
            details,
        )

    console.print(table)


def print_progress(current: int, total: int, label: str = "") -> None:
    with Progress() as progress:
        task = progress.add_task(f"[cyan]{label}...", total=total)
        progress.update(task, completed=current)


def print_recording_start() -> None:
    console.print(Panel.fit(
        "[bold yellow]Recording...[/bold yellow] Press [bold red]F9[/bold red] to stop.",
        title="autokeymouse",
    ))


def print_recording_done(script: Script) -> None:
    console.print(Panel.fit(
        f"[bold green]Recording complete![/bold green]\n"
        f"Events: {script.meta.event_count} | Duration: {script.meta.duration_ms}ms",
        title="autokeymouse",
    ))


def print_playback_start(script_name: str, times: int) -> None:
    console.print(Panel.fit(
        f"[bold cyan]Playing: {script_name}[/bold cyan] x{times}\n"
        f"Press [bold red]F9[/bold red] to stop.",
        title="autokeymouse",
    ))


def print_playback_done(result) -> None:
    status = "[bold yellow]stopped early[/bold yellow]" if result.stopped_early else "[bold green]completed[/bold green]"
    console.print(Panel.fit(
        f"Playback {status}\n"
        f"Cycles: {result.completed_cycles} | Time: {result.total_time_ms}ms",
        title="autokeymouse",
    ))


def print_script_list(scripts: list[dict]) -> None:
    table = Table(title="Recorded Scripts")
    table.add_column("Name", style="cyan")
    table.add_column("Date", style="green")
    table.add_column("Events", style="yellow")
    table.add_column("Duration", style="white")

    for s in scripts:
        table.add_row(
            s.get("name", ""),
            s.get("created", ""),
            str(s.get("event_count", 0)),
            f"{s.get('duration_ms', 0)}ms",
        )

    console.print(table)