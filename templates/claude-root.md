# {Project name}

{One paragraph: what the product is, for whom, which apps/services make it up,
and the language of customer-facing copy.}

## How to work with the docs

`docs/` is the textual model of this project: features and business rules,
every page and screen, contracts, decisions, open work. The system is
specified in [docs/global/docs-system.md](docs/global/docs-system.md).

- Before a task, open every doc below whose "Read when" matches it (usually
  more than one) before reading code. Docs orient; still read the code you change.
- If a doc and the code disagree, the code is the truth for behaviour: fix the
  doc in the same task.
- After a change, update the docs it touched, append decisions to
  `docs/project/decisions.md`, keep `docs/project/todo.md` current, then run
  `python3 docs/global/tools/docs_check.py` (`--fix` regenerates the index).
- Store something in auto memory only when the user asks; project knowledge
  goes in the docs.

## Repo map

```
{dir}/    {one line: what it is}
```

## Commands

| Task | Command |
|---|---|
| {Run} | `{command}` |
| {Test} | `{command}` |

## Rules for every task

- {A cross-cutting hard rule, one line, with a link to the doc that explains it.}

## Docs index

Generated from each doc's front matter by `docs_check.py --fix`; do not edit
between the markers.

<!-- docs-index:start -->
<!-- docs-index:end -->
