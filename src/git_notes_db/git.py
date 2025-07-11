import io

from collections.abc import Iterable
from collections.abc import Sequence
from pathlib import Path

from attrs import define
from git import Blob
from git import Commit
from git import IndexFile
from git import Repo
from git import Tree
from gitdb.base import IStream


@define()
class GitHelper:
    """
    Additional helper code for working with git
    """

    repo: Repo

    def create_file_blob(self, data: str | bytes, path: str | Path) -> Blob:
        """
        Create and store file blob in repo.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        if isinstance(path, str):
            path = Path(path)

        if path.is_absolute():
            raise ValueError(f"Must be relative path. Got: {path!r}")

        istream = IStream(b'blob', len(data), io.BytesIO(data))

        binsha = self.repo.odb.store(istream).binsha
        return Blob(self.repo, binsha, Blob.file_mode, str(path))

    def create_commit_in_memory(
        self,
        files: Iterable[tuple[Path | str, str | bytes]],
        message: str,
        *,
        parent_commits: Sequence[Commit] = (),
        tree: Tree | None = None,
    ):
        """
        Create simple commit using only memory/temporary files.
        """

        if tree is None:
            if len(parent_commits) == 1:
                tree = parent_commits[0].tree

        index: IndexFile
        if tree is None:
            index = IndexFile(self.repo)
        else:
            index = IndexFile.from_tree(self.repo, tree)

        del tree

        blobs: list[Blob] = [
            self.create_file_blob(data=data, path=path) for path, data in files
        ]

        if blobs:
            _ = index.add(blobs)

        new_tree = index.write_tree()

        return Commit.create_from_tree(
            self.repo,
            new_tree,
            parent_commits=list(parent_commits),
            message=message,
        )
