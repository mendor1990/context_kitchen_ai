---
description: The docs system spec — layout, doc types, front matter, maintenance loop, decisions, todo, memory policy, checks, bootstrap.
read_when: creating, moving, splitting or deleting a doc; writing a decision or todo item; unsure where a fact belongs; auditing docs; setting the system up in another project
---

# Docs system

A portable way to keep a project's knowledge in Markdown that a coding agent
(Claude Code first, any agent second) and humans read on demand. The docs are
the textual model of the project: every page and screen, feature, business
rule, decision and open question. The agent keeps them current as part of
every task, so a new session starts from the docs instead of re-reading the
codebase.

This file and the rest of `docs/global/` are project-agnostic. The kit lives
in its own repository; add it to any repository as a git submodule at
`docs/global/` ([README](README.md#add-to-a-new-project)) and follow
[Bootstrap](#bootstrap-in-a-new-project).

## Where the ideas come from

- **Claude Code memory**: `CLAUDE.md` is loaded into every session; other files
  are read only when needed. Keep `CLAUDE.md` under 200 lines; `@path` imports
  load at launch and save no context, so on-demand docs are plain links.
- **Context engineering**: the smallest set of high-signal tokens; keep
  lightweight identifiers (paths, links) and load content just in time;
  descriptive names and folders are retrieval signals.
- **AGENTS.md** (open standard): a README for agents — project overview,
  commands, conventions, nearest file wins.
- **Two-layer pattern**: a short always-loaded root with a routing index, plus
  task-specific docs, each with a "read when" trigger; docs change in the same
  change as the code; "prefer pointers to copies".
- **ADR / MADR**: decisions recorded with context, the choice and its
  consequences; superseded, never rewritten.
- **Diátaxis**: keep reference (what is), how-to (do X), and explanation (why)
  apart; here: feature and reference docs, subproject READMEs, decisions.
- **Docs-as-code and drift checks**: docs live in the repo, are reviewed with
  code, and deterministic checks catch broken links and stale docs.

## Principles

1. **Two layers.** `CLAUDE.md` holds only what every task needs: identity, how
   to use the docs, the index, commands, universal rules. Everything else is in
   `docs/`, opened on demand.
2. **Route by task.** Every doc declares what it holds and when to read it. The
   index in `CLAUDE.md` lists every doc with both.
3. **Current state only.** Docs say what *is*. History is git; *why* is the
   decision log; *next* is the todo. No changelogs, no "previously", no "new".
4. **One fact, one home.** State a fact once and link to it. Point to code
   (paths, symbols) instead of copying it.
5. **Co-change.** A change to behaviour, structure, contracts, commands or
   rules updates its docs in the same task. The task is not done until the
   docs match.
6. **Code is the truth for behaviour.** When a doc and the code disagree, read
   the code and fix the doc. If the code breaks a recorded rule or decision,
   report it to the user instead of silently "fixing" either.
7. **Verified, not guessed.** Write only what was read in code or told by the
   user. Unknowns become open questions in the todo; unconfirmed business
   claims are marked as such.
8. **Small, named, stable.** One topic per file, kebab-case names that say what
   is inside, ~300 lines (split past 500). Paths are identifiers: rename only
   with a reason, and fix every link.
9. **Deterministic checks over prose.** Links, front matter, the index, sizes
   and staleness are checked by `tools/docs_check.py`. Code style belongs to
   linters, not docs.
10. **Plain words.** No capitals or "IMPORTANT" for emphasis (agents over-apply
    such rules); a clear sentence is enough.

## Layout

```
CLAUDE.md                      always loaded: identity, docs rules, index, commands, universal rules
.claude/rules/*.md             optional: path-scoped pointers, loaded when matching files are touched
docs/
├── global/                    portable kit, a git submodule — never project facts
│   ├── README.md              what the kit is and how to install it
│   ├── docs-system.md         this spec
│   ├── templates/             a starting point for every doc type
│   └── tools/docs_check.py    checker and index generator
└── project/                   this project only
    ├── overview.md            product: what, for whom, channels, glossary, feature map
    ├── architecture.md        components, data flow, integrations, environments
    ├── development.md         local setup, services, ports, data, troubleshooting
    ├── deployment.md          environments, deploy, operations
    ├── decisions.md           decision log (ADR-lite), append-only
    ├── todo.md                open work, known issues, questions for the owner
    ├── features/<name>.md     one per business feature: the rules, across all subprojects
    └── <subproject>/          one folder per app/service/package
        ├── README.md          stack, structure, conventions, commands, how-tos, gotchas
        └── <topic>.md         reference: API, data model, screens, pages, …
```

- **Features own the business rules.** A rule that the backend enforces and
  two clients display is written once, in its feature doc, with a "Where it
  lives" table pointing at each implementation.
- **Subproject docs own the implementation**: structure, conventions, how to
  add things, per-screen behaviour, contracts. They link to features for rules.
- Create a file when its content exists; do not pre-create empty docs.
  Not every project has every file.
- The whole system — `CLAUDE.md`, `docs/`, `.claude/rules/` — is committed
  with the code; never gitignore it. Personal notes go in `CLAUDE.local.md`
  and personal settings in `.claude/settings.local.json`, both gitignored.

## Doc anatomy

Every doc under `docs/` (except `templates/`) starts with front matter that
`docs_check.py` parses. Simple `key: value` lines and `- item` lists only.

```yaml
---
description: One line — what this doc holds.
read_when: The task wording that should open it (names of features, screens, files, actions).
code:                       # optional: paths or globs this doc describes
  - app/src/orders/**
  - server/lib/src/endpoints/order.dart
verified: 2026-01-31        # optional: date the doc was last checked against `code`
max_lines: 800              # optional: a log meant to grow (decisions.md) raises the size warning
---
```

- `description` and `read_when` become the doc's index entry. Write
  `read_when` in the words a task would use ("checkout", "order status",
  "add an endpoint"), not a summary of the doc.
- `code` lets the checker warn when that code changed after `verified`. Set
  `verified` to today whenever you check or update the doc against its code.
- Body: `# Title`, one to three lines of scope, then the sections of the
  doc's type. Link docs with relative Markdown links; name code as
  `path/to/file.ext` and symbols in backticks. Add `path:line` only for spots
  that rarely move.

## Doc types

| Type | Location | Holds | Template |
|---|---|---|---|
| Root index | `CLAUDE.md` | identity, docs rules, index, commands, universal rules | [claude-root.md](templates/claude-root.md) |
| Overview | `project/overview.md` | product, users, channels, glossary, feature map | [overview.md](templates/overview.md) |
| Architecture | `project/architecture.md` | components, data flow, integrations, environments | [architecture.md](templates/architecture.md) |
| Feature | `project/features/*.md` | rules, states, flows, where implemented, copy, edge cases | [feature.md](templates/feature.md) |
| Subproject README | `project/<sub>/README.md` | stack and versions, structure, conventions, commands, how-tos, gotchas | [subproject-readme.md](templates/subproject-readme.md) |
| Screens / pages | `project/<sub>/screens.md` | per screen: route, purpose, data, actions, states | [screens.md](templates/screens.md) |
| Reference | `project/<sub>/<topic>.md` | API, data model, configuration — tables mirroring the code | none |
| Decision log | `project/decisions.md` | why: context, decision, consequences | [decisions.md](templates/decisions.md) |
| Todo | `project/todo.md` | open work, known issues, owner questions | [todo.md](templates/todo.md) |
| Ops | `project/development.md`, `deployment.md` | how to run, deploy, restore, troubleshoot | none |

## What goes where

| The fact | Its home |
|---|---|
| Needed by every task: commands, cross-cutting hard rules, a destructive-action guard | `CLAUDE.md`, one line each |
| What the product does (a business rule, a state machine, a limit) | `features/<feature>.md` |
| How a subproject is built, its conventions, how to add a thing | `<sub>/README.md` |
| An exact contract: endpoint, table, enum, route, screen | `<sub>/<reference>.md` |
| Why X and not Y; anything the owner decided | `decisions.md` |
| Work not done, a known bug, an unknown, an owner question | `todo.md` |
| Local setup, ports, data restore; environments and deploy | `development.md` / `deployment.md` |
| A detail about one function that only matters when reading it | a code comment |
| Machine- or person-specific notes (local SDK path) | `development.md` "maintainer machine" section, or `CLAUDE.local.md` |
| How the user wants the agent to behave, across projects | user memory or `~/.claude/CLAUDE.md` |
| Secrets, tokens, passwords, personal data | nowhere in docs |

## The working loop

**Before a task**

1. Read the index in `CLAUDE.md` and open every doc whose "read when" matches
   the task — usually more than one (the feature doc and the subproject doc).
2. Use the docs to orient: where things live, which rules apply, what was
   decided. Still read the code you are going to change.

**During the task**

- When something non-obvious turns up (a rule, a gotcha, a constraint), note
  it for the docs. When the user decides something, that is a decision.
- If a doc is wrong, fix it in this task, even if it is not about your change.

**Before reporting the task done**

1. Update every doc the change touched (table below); set `verified`.
2. A decision was made → append it to `decisions.md`; one was reversed → mark
   the old entry superseded.
3. Todo: delete what is finished; add gaps, bugs and questions you found.
4. A doc was added, renamed or removed → fix links and regenerate the index:
   `python3 docs/global/tools/docs_check.py --fix`.
5. Run `python3 docs/global/tools/docs_check.py`; fix errors, review warnings.
6. Say in the final report, in one line, which docs changed.

| You changed | Update |
|---|---|
| An endpoint, a model, a migration | the backend API / data-model doc, plus the features it affects |
| A screen or a page | the subproject's screens/pages doc, plus the features it shows |
| A business rule | its feature doc, including every client's part of it |
| A command, a tool, a version | `CLAUDE.md` commands, the subproject README, `development.md` |
| Deploy, infrastructure, config | `deployment.md`, `architecture.md` |
| A convention | the subproject README (and `CLAUDE.md` if it is universal) |
| A decision | `decisions.md`, linked from the docs it explains |

## Decisions

`project/decisions.md` is an append-only log in an ADR-lite format derived from
MADR. Write an entry when there were real alternatives and the choice has
lasting consequences, or when the owner decided something. A small convention
goes in the subproject README with its one-line reason instead.

```markdown
### D-012 Cart lives in the browser, not on the server

2026-03-02 · web · accepted

**Context.** What forced a choice: the constraint, the problem, the evidence.
**Decision.** What was chosen, stated as a rule.
**Consequences.** What follows, good and bad; what must stay true.
**Alternatives.** Optional: what was rejected and why.
```

- IDs are sequential and never reused. The title states the decision.
- Status: `proposed`, `accepted`, `superseded by D-NNN`, `rejected`.
- Supersede by adding a new entry and changing only the old one's status line.
  Do not edit an accepted entry's reasoning; add a new one.
- Docs link to entries (`decisions.md#d-012-…` or "D-012").
- Past ~600 lines, split by area into `decisions/<area>.md`, keeping the IDs.

## Todo

`project/todo.md` holds everything not done yet. Fixed sections: *Needs a
decision from the owner*, *Known issues*, one section per area, *Content and
data*, *Tooling*. Items:

```markdown
- [ ] **Short title** — the context in a sentence; where (`path` or [doc](link));
      what unblocks it. For an owner question: the options and a recommendation.
```

Delete an item when it is done (git keeps the history). Add an item for every
gap found while working, even when it is not fixed in this task.

## Memory, docs and CLAUDE.md

- **Docs** hold everything about the project. They are versioned, reviewed and
  shared; this is the default destination.
- **Auto memory** (`~/.claude/projects/<project>/memory/`) is used when the user
  asks to remember something, and for facts about the user or how they want
  to work. When such a request is about the project itself, also put it in the
  docs so the repo stays complete.
- **`CLAUDE.md`** carries only what every session needs. Instructions said in
  the chat are lost at compaction; if they should last, they go in a doc or in
  `CLAUDE.md`.

## Writing style

- English (the product's UI language only inside quoted UI copy, verbatim).
- Present tense, active voice, short sentences. Facts, not narrative.
- Rule first, then the reason in one clause, linking the decision.
- Tables for enumerations (endpoints, fields, routes, states); bullets for
  rules; numbered steps for procedures.
- Exact names: files, symbols, routes, enum values, settings, UI strings.
- Absolute dates (`2026-11-24`), never "recently" or "now".
- Mark what the owner has not confirmed and add a todo item for it.
- No secrets, no personal data, no filler, no marketing, no emoji.

## Sizes

- `CLAUDE.md`: under 200 lines (Claude Code warns above that and adherence
  drops). One index line per doc.
- A doc: aim for ~300 lines; split past 500 lines or 40,000 characters (files
  loaded on demand can be truncated past that).
- `description` ≤ ~20 words, `read_when` ≤ ~25 words.

## Checks — `tools/docs_check.py`

Python 3 standard library only, run from anywhere in the repo:

```bash
python3 docs/global/tools/docs_check.py          # check; exit 1 on errors
python3 docs/global/tools/docs_check.py --fix    # also rewrite the index in CLAUDE.md
python3 docs/global/tools/docs_check.py --no-git # skip the staleness check
```

| Check | Level |
|---|---|
| Front matter present, with `description` and `read_when` | error |
| Relative links in docs and `CLAUDE.md` resolve | error |
| The index block in `CLAUDE.md` matches the docs (`--fix` rewrites it) | error |
| Each `code` path or glob matches something | error |
| Code under `code` changed after `verified` (git log, or uncommitted edits) | warning |
| `CLAUDE.md` over 200 lines; a doc over 500 lines (or its `max_lines`) or 40,000 characters | warning |

The index lives between `<!-- docs-index:start -->` and
`<!-- docs-index:end -->` in `CLAUDE.md` (HTML comments are stripped before
Claude sees the file). Never edit inside the markers by hand.

## Audits

When asked to audit the docs, or when the checker reports many stale docs:
for each doc, re-read its `code`, confirm the main rules and contracts, fix
what drifted, delete what no longer exists, check that the todo items still
stand, set `verified`, and report what changed and what needs the owner.

## Bootstrap in a new project

1. Add the kit, unchanged, as a git submodule at `docs/global/`
   ([how](README.md#add-to-a-new-project)).
2. Ask the agent: "Set up the docs system from `docs/global/docs-system.md`."
3. The agent then:
   1. Surveys the repo: subprojects, stacks, commands (Makefile, scripts,
      package manifests), existing docs (`CLAUDE.md`, `AGENTS.md`, READMEs,
      `docs/`), auto memory, TODO comments.
   2. Creates `docs/project/` from the templates: overview, architecture,
      development, deployment, decisions, todo, one folder per subproject.
   3. Fills each subproject from the code: structure, conventions, commands;
      every screen or page; every endpoint, model and job.
   4. Writes a feature doc per business area from the code that enforces it.
   5. Moves existing docs into the structure (`git mv`), merges duplicates,
      fixes code comments that point at old paths, and leaves a one-line
      pointer README where humans expect one.
   6. Collects decisions from existing notes (only clear ones) and todo items
      from gaps, TODO comments and contradictions found.
   7. Writes `CLAUDE.md` from `templates/claude-root.md`, adds the index
      markers, runs `docs_check.py --fix`, then `docs_check.py`. Makes sure
      `.gitignore` does not exclude `CLAUDE.md`, `docs/` or `.claude/rules/`,
      and ignores `CLAUDE.local.md` and `.claude/settings.local.json`.
   8. Optionally adds `.claude/rules/` pointers (see below).
   9. Reports to the user: what was created, and the open questions only the
      owner can answer.

## Other agents and tools

- **AGENTS.md**: Claude Code reads `AGENTS.md` only when no `CLAUDE.md`
  exists. To serve several agents from one file, keep the shared content in
  `AGENTS.md` and make `CLAUDE.md` start with `@AGENTS.md` followed by
  Claude-specific lines. Prefer the import to a symlink: Claude Code's edit
  tools refuse to write through symlinks.
- **Path-scoped rules** (Claude Code): a `.claude/rules/<area>.md` file with
  `paths:` front matter loads only when Claude reads or edits a matching file.
  Use it for two-line pointers ("read `docs/project/<sub>/README.md` before
  editing; update docs in the same task"), never for copies of doc content.
  Template: [claude-rule.md](templates/claude-rule.md).
- **Hooks**: a Stop hook can run `docs_check.py` so drift shows up at the end
  of every turn. Configure it only when the user asks.
- **Everything in `docs/`** is plain Markdown, readable by any agent or human.
