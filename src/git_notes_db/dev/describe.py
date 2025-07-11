"""
Helper to describe
"""

import argparse
import sys

from collections.abc import Sequence
from pathlib import Path

from .commit_helpers import jj_with_message


def describe(args: None | Sequence[str] = None) -> None:
    """
    Describe with correct message via jj
    """
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    _ = parser.add_argument(
        "--edit",
        "-e",
        dest="edit",
        help="Edit message before updating description",
        default=False,
        action="store_true",
    )

    _ = parser.add_argument(
        "describe_args", nargs="*", help="Extra args passed to jj describe"
    )
    ctx = parser.parse_args(args)
    assert Path(".jj").exists(), "Expected jj repo"

    jj_with_message("describe", *ctx.describe_args, edit=ctx.edit)


if __name__ == "__main__":
    describe()
