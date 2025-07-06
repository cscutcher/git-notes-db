# git-notes-db

This tool helps store structured information in git-notes.
It aims to be usable manually, but also for creating other scripts.



Usage
=====

When setting value specify a name as the first argument (this will be `refs/notes/<name>`). In this example we use `test_results`.
The second argument is the commit this data is about.
The third argument is what to store, this can be anything that `jq` accepts, including standard JSON.

All operations must be run from within a git repository.

```console
$ git-notes-db test_results HEAD '{passed: false, older_results: []}'
```

To read the data back, omit the third argument.

```console
$ git-notes-db test_results HEAD
> {"passed": false, "older_results": []}
```

When updating, the jq expression gets any original value as an input (or null if no original value is stored). This allows for selective updating, or merging data.

```console
$ git-notes-db test_results HEAD '{passed: true, older_results: .older_results + [.passed]}'
$ git-notes-db test_results HEAD
> {"passed": true, "older_results": [false]}
```


Development Notes
=================

- Where possible, use asyncio everywhere.
- Ruff should be used to format code.
- Basedpyright and ruff should both be run for static testing.
- Write unit/integration tests suitable for pytest.
