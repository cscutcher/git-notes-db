import contextlib
import functools
import tempfile

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import overload

import nox

from nox.sessions import Session


if TYPE_CHECKING:
    from nox._decorators import Func


@overload
def _uv_session[R](fn: Callable[..., R], /) -> 'Func': ...


@overload
def _uv_session[R](
    fn: None = None,
    /,
    **session_kwargs,
) -> Callable[[Callable[..., Any]], 'Func']: ...


def _uv_session[R](fn=None, /, **session_kwargs):
    """
    Helper for dev session.
    """
    if fn is not None:
        assert not session_kwargs
        return _uv_session()(fn)

    assert "venv_backend" not in session_kwargs

    def _wrap(
        fn_inner: Callable[..., R],
        /,
    ):
        """
        Wrap session command
        """

        @nox.session(venv_backend="uv", **session_kwargs)
        @functools.wraps(fn_inner)
        def _wrapper(session: nox.Session, *args, **kwargs) -> R:
            _ = session.run_install(
                "uv",
                "sync",
                "--dev",
                "--frozen",
                f"--python={session.virtualenv.location}",
                env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
                silent=True,
            )
            return fn_inner(session, *args, **kwargs)

        return _wrapper

    return _wrap


@nox.session(python=False)
def tests(session: Session):
    """
    Run all tests
    """
    session.notify("pytest")


@_uv_session
def pytest(session: Session):
    """
    Run pytest
    """
    _ = session.run("pytest", *session.posargs)


@_uv_session
def ruff(session: Session):
    """
    Run all tests
    """
    _ = session.run("ruff", "check", *session.posargs)


@nox.session(python=False)
def lint(session: Session):
    """
    Run all tests
    """
    session.notify("ruff")


@contextlib.contextmanager
def _create_commit_message(session: Session):
    """
    Create commit message with commitizen
    """
    _ = session.run("jj", "diff", "--no-pager", external=True)
    with tempfile.NamedTemporaryFile(prefix="COMMIT_EDITMSG") as msg_file:
        _ = session.run(
            "cz",
            "commit",
            "--dry-run",
            "--write-message-to-file",
            msg_file.name,
            "--edit",
        )
        _ = session.run("cz", "check", "--commit-msg-file", msg_file.name)
        yield Path(msg_file.name)


@_uv_session
def commit(session: Session):
    """
    Create commit via commitizen
    """

    assert Path(".jj").exists(), "Expected jj repo"

    with _create_commit_message(session) as message:
        _ = session.run(
            "jj",
            "commit",
            "--message",
            message.open('r').read(),
            *session.posargs,
            external=True,
        )


nox.options.sessions = ["lint", "pytest"]
