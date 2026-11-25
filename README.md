---
description: The portable docs kit — contents, adding it to a project as a git submodule, cloning, updating.
read_when: moving the docs system to another project; asking what docs/global is; cloning a project that uses the kit; updating the kit or its submodule pointer
---

# Docs kit (portable)

A self-contained kit for running a project's knowledge as docs that an AI
agent maintains. Nothing in it is about one project. The kit lives in its own
repository, and every project includes it as a git submodule at
`docs/global/`: the project pins one kit commit and moves to a newer one only
when the kit is updated there.

| File | What it is |
|---|---|
| [docs-system.md](docs-system.md) | The spec: layout, doc types, front matter, the working loop, decisions, todo, memory policy, checks, bootstrap |
| [templates/](templates/) | Starting points: root `CLAUDE.md`, overview, architecture, feature, subproject README, screens, decisions, todo, path rule |
| [tools/docs_check.py](tools/docs_check.py) | Checker and index generator (Python 3 standard library) |

## Add to a new project

1. From the root of the target repository:

   ```bash
   git submodule add -b main https://github.com/mendor1990/context_kitchen_ai.git docs/global
   ```

   The path must be `docs/global`: the checker, the templates and the doc
   links expect it (without a path git names the folder `context_kitchen_ai`).
   `-b main` makes `git submodule update --remote` follow the kit's `main`.
   Git clones the kit and stages `.gitmodules` and `docs/global` (a pointer to
   one kit commit); commit both with the project.
2. Start a Claude Code session there and say:
   *"Set up the docs system from `docs/global/docs-system.md`."*
3. The agent follows [Bootstrap](docs-system.md#bootstrap-in-a-new-project):
   surveys the repo, creates `docs/project/` and `CLAUDE.md` from the
   templates, moves existing docs in, generates the index, runs the checker,
   and lists the questions only you can answer.

From then on the agent keeps the docs current as part of every task
([the working loop](docs-system.md#the-working-loop)). Ask for
"audit the docs" now and then; ask to "remember" something only when it is
about you rather than the project.

A project that holds a copied `docs/global/` folder switches to the
submodule as below. The copy is deleted, so first check that it has no edits
the kit lacks (`diff -r docs/global <a clone of the kit>`).

```bash
git rm -r docs/global
rm -rf docs/global        # untracked leftovers such as .DS_Store
git submodule add -b main https://github.com/mendor1990/context_kitchen_ai.git docs/global
python3 docs/global/tools/docs_check.py --fix
```

## Clone a project that uses the kit

```bash
git clone --recurse-submodules <project-url>
```

A clone made without `--recurse-submodules` has an empty `docs/global/`: the
links in `CLAUDE.md` lead nowhere and the checker is missing. Fill it from the
project root:

```bash
git submodule update --init
```

A `git pull` or a branch switch can move the kit pointer without updating the
folder. Run `git submodule update` after it, or set
`git config --global submodule.recurse true` once and git does it on every
pull, checkout and switch.

Commits from before a project switched to the submodule hold the kit as plain
files, and checking one out fails with "untracked working tree files would be
overwritten". Run `git submodule deinit -f docs/global` first; after coming
back, run `git submodule update --init`.

## Update the kit

`git submodule status` shows which kit commit a project uses. To take the
latest kit into a project:

```bash
git submodule update --remote docs/global
python3 docs/global/tools/docs_check.py --fix   # the kit's front matter feeds the index in CLAUDE.md
```

Then commit `docs/global` together with `CLAUDE.md`.

To improve the kit:

1. Edit a standalone clone of the kit repository, or `docs/global/` inside a
   project. A submodule is usually on a detached commit, so put it on the
   branch first: `git -C docs/global switch main && git -C docs/global pull`.
2. Keep the kit free of project names, paths and facts: those belong in
   `docs/project/`.
3. Commit and push in the kit repository (inside a project that means running
   `git commit` and `git push` in `docs/global/`).
4. In the project where you edited, run `docs_check.py --fix` and commit
   `docs/global` (now at the new commit) with `CLAUDE.md`. Other projects take
   the change with the update above.

The submodule URL is HTTPS, so anyone can clone without a GitHub key. To push
over SSH from such a clone, set once:
`git config --global url."git@github.com:".pushInsteadOf "https://github.com/"`.
