---
description: Test plan for {feature} — test data, setup, cases with exact expected results, the status of each case.
read_when: testing {feature} by hand; after changing {its screens or flows}; picking test data for {feature}
verified: {YYYY-MM-DD}
---

# {Feature} — test plan

{What is checked, and on what: an emulator, a device, a store sandbox. Link the
feature doc for the rules, and the shared device setup in development.md.}

## Test data

| Key | The data must have | Id |
|---|---|---|
| {T1} | {the condition a case needs} | {an id, or "none on YYYY-MM-DD"} |

## Setup

- {Only what is specific to these cases; shared device setup lives in
  development.md.}

## Cases

Texts in «» must match exactly.

| # | Data | Steps | Expected |
|---|---|---|---|
| {A1} | {T1} | {what to do} | {the exact result} |

## Status

Last run {YYYY-MM-DD} on {build and device}.

- **Passed:** {case ids}
- **Open:** {case ids} — {why: no data yet, needs a sign-out, …}
- **Findings:** {what the run found; every bug also goes to todo.md}

Rewrite this section after each run; git keeps the earlier ones.
