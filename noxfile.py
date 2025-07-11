import functools

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


@nox.session(python=False, requires=["pytest"])
def tests(session: Session):
    """
    Run all tests
    """


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


@nox.session(python=False, requires=["ruff"])
def lint(session: Session):
    """
    Run all tests
    """


@_uv_session(tags=["sync"])
def format(session: Session):
    """
    Perform formatting like tasks
    """
    _ = session.run("ruff", "format", *session.posargs)


@nox.session(python=False, requires=["lint", "tests"], tags=["checks"])
def checks(session: Session):
    """
    Check and commit
    """
    session.notify("lint")
    session.notify("tests")


@_uv_session(tags=["sync"])
def sync(session: Session):
    """
    Sync anything that needs to be synced. Idempotent.
    """
    _ = session.run("cz", "changelog")


@_uv_session(requires=["checks"])
def bump(session):
    """
    Perform version bump
    """
    session.run("cz", "bump", *session.posargs)


@nox.session(python=False)
def push(session: Session):
    """
    Push changes and tags to remove repos
    """
    _ = session.run("jj", "git", "push", "--remote", "gitlab")
    _ = session.run("jj", "git", "push", "--remote", "github")
    _ = session.run("git", "push", "--tags", "gitlab")
    _ = session.run("git", "push", "--tags", "github")


nox.options.sessions = ["lint", "pytest", "sync"]
