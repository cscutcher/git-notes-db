import enum
import json

from abc import ABC
from abc import abstractmethod
from collections.abc import Awaitable
from collections.abc import Iterable
from functools import cached_property
from pathlib import Path
from typing import Callable
from typing import Protocol
from typing import Self
from typing import cast
from typing import override

from attrs import Factory
from attrs import define
from attrs import field
from git import Commit
from git import Repo
from pydantic import BaseModel
from pydantic import JsonValue
from rich.console import Console
from rich.json import JSON

from git_notes_db.helpers import CommitDB
from git_notes_db.helpers import CommitNote

from . import jq


class IOutput(Protocol):
    pretty: bool


class BaseContext(BaseModel):
    """
    Context passed into `_`
    """

    cwd: Path
    rich_traceback: bool
    name: str
    pretty: bool


class GetContext(BaseContext):
    commit: str


class SetContext(BaseContext):
    commit: str
    expr: str


def _repo_factory[ContextT: BaseContext](
    inst: 'Command[ContextT]',
):
    return Repo(inst.context.cwd)


@define()
class Command[
    ContextT: BaseContext,
](ABC):
    """
    Command for
    """

    context: ContextT = field()
    console: Console = field(factory=Console)
    repo: Repo = field(
        default=Factory(
            cast(Callable[[Self], Repo], _repo_factory), takes_self=True
        )
    )

    @cached_property
    def _db(self) -> CommitDB:
        return CommitDB(repo=self.repo, db_name=self.context.name)

    def _dump_json(self, data: JsonValue):
        """
        Print json to output
        """
        _dump_json(self.context, self.console, data)

    @abstractmethod
    async def __call__(self) -> None: ...


@define()
class Set(Command[SetContext]):
    @override
    async def __call__(self):
        """
        Execute body of script
        """
        note = self._db.get(self.context.commit)
        result = await note.update(self.context.expr)
        self._dump_json(result)


@define()
class Get(Command[GetContext]):
    @override
    async def __call__(self):
        result = await self._db.get(self.context.commit).get()
        self._dump_json(result)


class JsonOutput(enum.StrEnum):
    LIST = enum.auto()
    DICT = enum.auto()


class IJsonCommand(IOutput, Protocol):
    json_out: None | JsonOutput


class GetAllContext(BaseContext):
    json_out: None | JsonOutput
    expr: str | None


def _dump_json(context: IOutput, console: Console, data: JsonValue):
    """
    Print json to output
    """
    if context.pretty:
        console.print(JSON.from_data(data))
    else:
        console.print(json.dumps(data, separators=(',', ':')))


async def _default_eval(note: CommitNote):
    return await note.get()


async def _dump_all(
    context: IJsonCommand,
    console: Console,
    notes: Iterable[tuple[Commit, CommitNote]],
    *,
    eval_note: Callable[[CommitNote], Awaitable[JsonValue]] = _default_eval,
):
    match context.json_out:
        case None:
            for commit, note in notes:
                if context.pretty:
                    console.rule(
                        f"{commit.hexsha} - {commit.message.splitlines()[0]}",
                        align="left",
                    )
                else:
                    console.print(commit.hexsha)
                result = await eval_note(note)

                _dump_json(context, console, result)
                console.print("")

        case JsonOutput.LIST:
            _dump_json(
                context,
                console,
                [
                    {
                        "commit": commit.hexsha,
                        "result": await eval_note(note),
                    }
                    for commit, note in notes
                ],
            )
        case JsonOutput.DICT:
            _dump_json(
                context,
                console,
                {
                    commit.hexsha: await eval_note(note)
                    for commit, note in notes
                },
            )


@define()
class GetAll(Command[GetAllContext]):
    @cached_property
    def program(self):
        if self.context.expr:
            return jq.compile(self.context.expr)
        return None

    async def eval_note(self, note: CommitNote):
        """
        Evaluate single note
        """
        if self.program is None:
            return await note.get()

        return await note.jq(self.program)

    @override
    async def __call__(self):
        await _dump_all(
            self.context,
            self.console,
            self._db.iter_all_notes(),
            eval_note=self.eval_note,
        )


class MatchContext(BaseContext):
    json_out: None | JsonOutput
    expr: str


@define()
class Match(Command[MatchContext]):
    @cached_property
    def program(self):
        return jq.compile(self.context.expr)

    @override
    async def __call__(self):
        # Can't make this an iterator withut making _dump_all expect a
        # async iterator
        # TODO: Do that, assuming I get around to actually making anything
        # use async.
        notes = [
            (commit, note)
            for commit, note in self._db.iter_all_notes()
            if await note.jq(self.program)
        ]

        await _dump_all(
            self.context,
            self.console,
            notes,
        )
