"""
Helper to commit
"""

import argparse
import subprocess
import sys

from collections.abc import Sequence
from pathlib import Path

from .commit_helpers import jj_with_message


def commit(args: None | Sequence[str] = None) -> None:
    """
    Commit with correct message via jj
    """
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser()
    _ = parser.add_argument(
        "--edit",
        "-e",
        dest="edit",
        help="Edit message before committing",
        default=False,
        action="store_true",
    )
    _ = parser.add_argument(
        "--interactive",
        "-i",
        action="append_const",
        const="-i",
        dest="commit_args",
        help="Select which changes to commit.",
    )

    _ = parser.add_argument(
        "commit_args", nargs="*", help="Extra args passed to jj commit"
    )
    ctx = parser.parse_args(args)
    assert Path(".jj").exists(), "Expected jj repo"

    subprocess.run(("uv", "run", "nox", "-t", "checks"), check=True)
    jj_with_message("commit", *ctx.commit_args, edit=ctx.edit)


if __name__ == "__main__":
    commit()
