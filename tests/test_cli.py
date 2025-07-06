import json

from io import StringIO

import pytest

from attrs import define
from git import Repo
from rich.console import Console

from git_notes_db.cli import main


@pytest.fixture
def git_repo_fixture(tmp_path):
    """
    Create a repo for test
    """
    repo = Repo.init(tmp_path)

    with (tmp_path / "some_file").open("w") as txt_io:
        txt_io.write("foo")

    repo.index.add("some_file")
    repo.index.commit("Initial commit")
    with repo:
        yield repo


@define()
class CommandFailure(Exception):
    exception: Exception
    output: str


def run_main(*args: *tuple[str, ...], decode: bool = True):
    """
    Run main and parse result
    """
    console_io = StringIO()
    console = Console(file=console_io, color_system=None)

    try:
        main(args=args, console=console)
    except Exception as exc:
        raise CommandFailure(
            exception=exc, output=console_io.getvalue()
        ) from exc

    if decode:
        return json.loads(console_io.getvalue())
    return console_io.getvalue()


def test_cli(git_repo_fixture: Repo):
    """
    Test the cli by running through example in readme
    """
    repo = git_repo_fixture

    def _run(*args):
        return run_main("-C", str(repo.working_dir), *args)

    assert _run("get", "test", "HEAD") is None
    _ = _run("set", "test", "HEAD", "{passed: false, older_results: []}")
    assert _run("get", "test", "HEAD") == {
        "passed": False,
        "older_results": [],
    }
    _ = _run(
        "set",
        "test",
        "HEAD",
        '{passed: true, older_results: .older_results + [.passed]}',
    )
    assert _run("get", "test", "HEAD") == {
        "passed": True,
        "older_results": [False],
    }
