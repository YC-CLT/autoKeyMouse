import argparse
import ctypes
import sys

from cli.commands import (
    handle_inspect,
    handle_list,
    handle_play,
    handle_record,
    register_commands,
)
from engine.logger import setup_logging


def main() -> None:
    setup_logging()
    ctypes.windll.user32.SetProcessDPIAware()
    parser = argparse.ArgumentParser(
        prog="autokeymouse",
        description="Keyboard/mouse recording and playback tool for Windows",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    register_commands(subparsers)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    handlers = {
        "record": handle_record,
        "play": handle_play,
        "list": handle_list,
        "inspect": handle_inspect,
    }

    handler = handlers.get(args.command)
    if handler is not None:
        exit_code = handler(args)
        sys.exit(exit_code)
    elif args.command == "tui":
        from tui.app import run_tui
        run_tui()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()