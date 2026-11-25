---
description: What the portable docs kit is, what is in it, and how to install it in another project.
read_when: moving the docs system to another project; asking what docs/global is; updating the kit itself
---

# Docs kit (portable)

`docs/global/` is a self-contained kit for running a project's knowledge as
docs that an AI agent maintains. Nothing in it is about one project, so it can
be copied as-is into any repository.

| File | What it is |
|---|---|
| [docs-system.md](docs-system.md) | The spec: layout, doc types, front matter, the working loop, decisions, todo, memory policy, checks, bootstrap |
| [templates/](templates/) | Starting points: root `CLAUDE.md`, overview, architecture, feature, subproject README, screens, decisions, todo, path rule |
| [tools/docs_check.py](tools/docs_check.py) | Checker and index generator (Python 3 standard library) |

## Install in another project

1. Copy this folder to `docs/global/` in the target repository.
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

## Updating the kit

Improve the kit in one project, then copy `docs/global/` to the others. Keep
it free of project names, paths and facts: those belong in `docs/project/`.
