# git-notes-db

[![License](https://img.shields.io/badge/license-Unlicense-blue.svg)](LICENSE)

This tool helps store structured information in git-notes.
It aims to be usable manually, but also for creating other scripts.

Usage
=====

When setting value specify a name as the first argument (this will be
`refs/notes/<name>`). In this example we use `test_results`.
The second argument is the commit this data is about.
The third argument is what to store, this can be anything that `jq` accepts, including standard JSON.

All operations must be run from within a git repository.

```console
$ git-notes-db set test_results HEAD '{passed: false, older_results: []}'
```

To read the data back;

```console
$ git-notes-db get test_results HEAD
> {"passed": false, "older_results": []}
```

When updating, the jq expression gets any original value as an input (or null
if no original value is stored). This allows for selective updating, or merging
data.

```console
$ git-notes-db set test_results HEAD '{passed: true, older_results: .older_results + [.passed]}'
$ git-notes-db get test_results HEAD
> {"passed": true, "older_results": [false]}
```

Other commands
--------------

`get_all`

It's also possible to get all known results with `get_all`. This also accepts
jq expressions which modify the output results.

`match`

Return's results matching supplied jq expression.


Todo
====

- [ ] Allow limiting queries/get by git revision range.
- [ ] Add subcommand to run some executable and store result.
      See git-branchless for inspiration.
        - Could make nice tui with textual.
- [ ] Package and push to pypi.
- [ ] Nix flake.
- [ ] Add helper to `push` given notes to a remote.
- [ ] Add helper to automatically configure git to fetch notes from remote.
- [ ] Add note merge helper. Use jq expression to handle merge.
- [ ] Add ability to specify a key (e.g. message).
      When this key is present on a result that's being set, also update a
      secondary *human readable* note for including in git log output with
      `notes.displayRef`.
- [ ] Add toggle for `match` that outputs just commits newline separated.
- [ ] Add option for `match` and `get_all` that stops searching after `n`
      results are outputted.
- [ ] Add option for `match` that fails if number of results is outside
      a given range.
- [ ] githooks / ci.
- [ ] More tutorial with usage examples.
- [ ] Feel like I've reinvented the wheel with the way I've built up the cli
      commands. I've not seen the state of CLI helper libraries recently.
      Maybe try [Typer](https://typer.tiangolo.com/).
      or [felix-martel/pydanclick: Add click options from a Pydantic
      model](https://github.com/felix-martel/pydanclick)

Development Notes
=================
- Haven't decided whether I want to primarily use
  [github](https://github.com/cscutcher/git-notes-db) or
  [gitlab](https://gitlab.com/cscutcher-public/git-notes-db).
- A bit over-engineered. Trying out some stuff.
- Trying out jujutsu VCS, commits might be weird until I work it out.
- Had originally planned to use more asyncio. Right now a bunch of stuff is
  async that probably doesn't need to be.
  Will leave this behind incase I end up wanting to parallelise things in
  future.
- Ruff should be used to format code.
- Basedpyright and ruff should both be run for static testing.
- Write unit/integration tests suitable for pytest.
