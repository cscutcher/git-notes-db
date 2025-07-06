#!/usr/bin/env python3
"""CLI for git-notes-db: store and access structured data in git-notes."""

import argparse
import asyncio
import sys

from collections.abc import Sequence
from functools import partial
from pathlib import Path
from typing import cast

from rich.console import Console

from .commands import Get
from .commands import GetAll
from .commands import GetAllContext
from .commands import GetContext
from .commands import JsonOutput
from .commands import Match
from .commands import MatchContext
from .commands import Set
from .commands import SetContext


async def async_main(
    args: Sequence[str] | None = None, console: Console | None = None
):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Store and access structured data in git-notes."
    )

    def add_name(parser: argparse.ArgumentParser):
        _ = parser.add_argument(
            "name",
            help="notes namespace (refs/notes/<name>)",
        )

    def add_commit(parser: argparse.ArgumentParser):
        _ = parser.add_argument(
            "commit",
            help="commit-ish to associate notes with",
        )

    def add_expr(parser: argparse.ArgumentParser):
        _ = parser.add_argument(
            "expr",
            help=("jq expression to apply"),
        )

    def add_json(parser: argparse.ArgumentParser):
        _ = parser.add_argument(
            "--json",
            dest="json_out",
            nargs="?",
            help="Ouput as single json structure. If `list` output list of mappings {commit: , result: }. If. If `dict` output as single dict `{commit: result}`",
            const=JsonOutput.DICT,
        )

    _ = parser.add_argument(
        "-C",
        type=Path,
        dest="cwd",
        help="Run in given directory",
        default=Path.cwd(),
    )

    _ = parser.add_argument(
        "--no-rich-traceback",
        dest="rich_traceback",
        default=True,
        action="store_false",
    )

    _ = parser.add_argument(
        "--no-pretty",
        dest="pretty",
        default=True,
        action="store_false",
        help="Try to ensure output is machine readable",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser(
        "set", help="Set a single commits entry using jq expression"
    )
    add_name(set_parser)
    add_commit(set_parser)
    add_expr(set_parser)

    get_parser = subparsers.add_parser(
        "get", help="Get a single result by commit id"
    )
    add_name(get_parser)
    add_commit(get_parser)

    get_all_parser = subparsers.add_parser(
        "get_all",
        help="Get all results stored, optionally applying jq expression.",
    )
    add_name(get_all_parser)
    add_expr(get_all_parser)
    add_json(get_all_parser)

    match_parser = subparsers.add_parser(
        "match", help="Return all results that match jq expression `expr`"
    )
    add_name(match_parser)
    add_expr(match_parser)
    add_json(match_parser)

    raw_context = parser.parse_args(args=args)

    # Slightly weird initialisation of the helper below due to trying to get
    # typing right. Whether it's worth it...?

    match cast(str, raw_context.command):
        case "set":
            context = SetContext.model_validate(
                raw_context, from_attributes=True
            )
            helper_factory = partial(Set, context=context)
        case "get":
            context = GetContext.model_validate(
                raw_context, from_attributes=True
            )
            helper_factory = partial(Get, context=context)
        case "get_all":
            context = GetAllContext.model_validate(
                raw_context, from_attributes=True
            )
            helper_factory = partial(GetAll, context=context)
        case "match":
            context = MatchContext.model_validate(
                raw_context, from_attributes=True
            )
            helper_factory = partial(Match, context=context)

        case _ as command:
            raise ValueError(f"Unexpected command {command}")

    if console is None:
        if context.pretty:
            console = Console()
        else:
            console = Console(color_system=None)

    helper = helper_factory(console=console)

    await helper()


def main(args: Sequence[str] | None = None, console: Console | None = None):
    """Entry point for git-notes-db CLI."""
    asyncio.run(async_main(args=args, console=console))
