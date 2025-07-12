"""
Run before bumping version by cz
"""

import os
import subprocess
import sys

from collections.abc import Sequence
from typing import TypeIs

from git import Repo
from git import TagObject
from git.types import AnyGitObject
from rich.console import Console
from rich.prompt import Confirm


def is_tag(inp: AnyGitObject) -> TypeIs[TagObject]:
    return inp.type == "tag"


def cz_pre_bump(args: None | Sequence[str] = None) -> None:
    """
    Ran before bumping version with cz
    """
    console = Console()

    if args is None:
        args = sys.argv[1:]

    assert not args, "No arguments expected"
    console.print("Preparing to bump version...\n")

    repo = Repo()
    last_tag = os.environ["CZ_PRE_CURRENT_TAG_VERSION"]
    last_version_tag = repo.rev_parse(last_tag)
    assert is_tag(last_version_tag), "Expected tag name"

    last_version_commit = last_version_tag.object
    revset = f"HEAD - {last_version_commit.hexsha}"

    console.print(
        f"Last commit had tag [bold]{last_tag}[/] with sha [bold]{last_version_commit.hexsha}[/]\n"
    )
    console.print("Will contain the following commits;")
    _ = subprocess.run(("git", "branchless", "query", revset), check=True)

    console.print("\n\nRunning checks against new commits...")

    try:
        _ = subprocess.run(
            (
                "git",
                "branchless",
                "test",
                "run",
                "-s",
                "worktree",
                "-x",
                'uv run nox -t checks',
                revset,
            ),
            check=True,
        )
    except Exception:
        console.print_exception(show_locals=True)
        console.rule()
        console.print(
            ":warning: [bold red]CHECKING PREVIOUS COMMITS FAILED[/]\n\n"
        )
        should_continue: bool = Confirm.ask("Continue anyway?", default=False)
        if should_continue:
            return
        raise

    console.print(
        "\n[green]Commits pass checks. Continuing to bump version[/]"
    )


if __name__ == "__main__":
    cz_pre_bump()
