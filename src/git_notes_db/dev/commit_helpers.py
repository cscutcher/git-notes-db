"""
Helper for jj and git related tasks
"""

import contextlib
import subprocess
import tempfile

from collections.abc import Sequence
from pathlib import Path
from typing import Literal


@contextlib.contextmanager
def _create_commit_message(*extra_args: str):
    """
    Create commit message with commitizen
    """
    _ = subprocess.run(("jj", "diff", "--no-pager"), check=True)

    with tempfile.NamedTemporaryFile(prefix="COMMIT_EDITMSG") as msg_file:
        _ = subprocess.run(
            (
                "cz",
                "commit",
                "--dry-run",
                "--write-message-to-file",
                msg_file.name,
                *extra_args,
            ),
            check=True,
        )
        _ = subprocess.run(
            ("cz", "check", "--commit-msg-file", msg_file.name), check=True
        )
        yield Path(msg_file.name)


def jj_with_message(
    command: Literal["commit", "describe"],
    *extra_args: str,
    edit: bool = False,
):
    """
    Run a jj command after gathering message from user
    """
    cz_extra_args: Sequence[str] = ("--edit",) if edit else ()
    with _create_commit_message(*cz_extra_args) as message:
        _ = subprocess.run(
            (
                "jj",
                command,
                "--message",
                message.open('r').read(),
                *extra_args,
            ),
            check=True,
        )
