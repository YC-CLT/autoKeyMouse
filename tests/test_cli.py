import argparse
from unittest.mock import MagicMock, patch

import pytest

from config import SHOT_RADIUS, MOUSE_MOVE_INTERVAL_MS
from cli.commands import (
    handle_inspect,
    handle_list,
    handle_play,
    handle_record,
    register_commands,
)


class TestRegisterCommands:
    def test_all_subcommands_registered(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args(["record"])
        assert args.command == "record"

    def test_play_subcommand_registered(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args(["play", "test_script"])
        assert args.command == "play"
        assert args.script == "test_script"

    def test_list_subcommand_registered(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args(["list"])
        assert args.command == "list"

    def test_inspect_subcommand_registered(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args(["inspect", "test_script"])
        assert args.command == "inspect"
        assert args.script == "test_script"

    def test_tui_subcommand_registered(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args(["tui"])
        assert args.command == "tui"


class TestRecordDefaults:
    def test_record_defaults(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args(["record"])
        assert args.output is None
        assert args.record_move is True
        assert args.move_interval == MOUSE_MOVE_INTERVAL_MS
        assert args.shot_radius == SHOT_RADIUS
        assert args.no_shot is False
        assert args.no_compress is False

    def test_record_custom_options(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args([
            "record", "--output", "my_task", "--no-record-move",
            "--move-interval", "100", "--shot-radius", "80", "--no-shot", "--no-compress",
        ])
        assert args.output == "my_task"
        assert args.record_move is False
        assert args.move_interval == 100
        assert args.shot_radius == 80
        assert args.no_shot is True
        assert args.no_compress is True


class TestPlayDefaults:
    def test_play_defaults(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args(["play", "test_script"])
        assert args.script == "test_script"
        assert args.times == 1
        assert args.speed == 1.0
        assert args.match is False

    def test_play_custom_options(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args([
            "play", "test_script", "--times", "5", "--speed", "2.0", "--match",
        ])
        assert args.times == 5
        assert args.speed == 2.0
        assert args.match is True


class TestListDefaults:
    def test_list_defaults(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args(["list"])
        assert args.dir is None
        assert args.json is False

    def test_list_json_flag(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args(["list", "--json"])
        assert args.json is True


class TestInspectDefaults:
    def test_inspect_args(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        register_commands(subparsers)

        args = parser.parse_args(["inspect", "test_script"])
        assert args.script == "test_script"