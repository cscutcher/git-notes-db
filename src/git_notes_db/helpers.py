import json

from pathlib import Path

from attrs import define
from attrs import field
from attrs.setters import frozen
from git import Blob
from git import Commit
from git import Object
from git import Reference
from git import Repo
from git import Tree
from pydantic import JsonValue
from pydantic import TypeAdapter

from git_notes_db.git import GitHelper

from . import jq


@define()
class CommitDB:
    repo: Repo = field(on_setattr=frozen)
    db_name: str = field(on_setattr=frozen)

    @property
    def repo_helper(self):
        return GitHelper(self.repo)

    @property
    def notes_ref(self):
        return Reference.from_path(self.repo, f"refs/notes/{self.db_name}")

    @property
    def notes_commit(self) -> Commit | None:
        if self.notes_ref_exists:
            assert isinstance(self.notes_ref.commit, Commit)  # Type guard
            return self.notes_ref.commit
        return None

    @property
    def notes_tree(self) -> Tree | None:
        if commit := self.notes_commit:
            return commit.tree
        return None

    @property
    def notes_ref_exists(self):
        """
        Does the notes ref currently exist
        """
        return Path(self.notes_ref.abspath).exists(follow_symlinks=True)

    def get(self, commit: Commit | str) -> "CommitNote":
        if isinstance(commit, str):
            commit = self.repo.commit(commit)

        return CommitNote(db=self, target_commit=commit)

    def iter_all_notes(self):
        if not self.notes_ref_exists:
            return
        tree: Tree = self.notes_ref.commit.tree

        blob: Object
        for blob in tree.blobs:
            commit = self.repo.commit(blob.name)
            yield commit, CommitNote(db=self, target_commit=commit)


def _jq_field_validator(jq_program: str | jq.Program) -> jq.Program:
    """
    Normalise a jq function
    """
    if isinstance(jq_program, str):
        return jq.compile(jq_program)
    return jq_program


type JQProgramField = str | jq.Program


@define()
class CommitNote:
    db: CommitDB = field(on_setattr=frozen)
    target_commit: Commit = field(on_setattr=frozen)

    async def get(self) -> JsonValue:
        """
        Get existing value
        """
        if not self.db.notes_ref_exists:
            return None

        hexsha = self.target_commit.hexsha

        try:
            tree = self.db.notes_tree
            assert tree
            blob_result = tree / hexsha
            assert isinstance(blob_result, Blob)  # Type guard
            blob: Blob = blob_result
        except KeyError:
            return None

        adapter: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
        raw: str = blob.data_stream.read().decode("utf-8")
        return adapter.validate_json(raw)

    async def set(self, data: JsonValue):
        """
        Set value. Creating new ref if needed.
        """
        parent_commits: list[Commit] = []
        if commit := self.db.notes_commit:
            parent_commits = [commit]
        else:
            parent_commits = []

        commit = self.db.repo_helper.create_commit_in_memory(
            ((self.target_commit.hexsha, json.dumps(data)),),
            message="Note added by git-notes-db\n",
            parent_commits=parent_commits,
        )

        _ = self.db.notes_ref.set_commit(commit)

    async def jq(self, jq_program: JQProgramField) -> JsonValue:
        """
        Execute jq program against current value
        """
        jq_program = _jq_field_validator(jq_program)
        orig_value = await self.get()

        result_values: list[JsonValue] = list(jq_program.input(orig_value))

        if len(result_values) < 1:
            return None
        if len(result_values) > 1:
            return result_values
        return result_values[0]

    async def update(self, jq_expression: JQProgramField) -> JsonValue:
        """
        Update current value using jq expression
        """
        new_value = await self.jq(jq_expression)
        await self.set(new_value)
        return new_value
