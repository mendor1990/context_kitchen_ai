---
description: System architecture — components, how they talk, shared code, data ownership, environments.
read_when: a change spans several subprojects; adding a service or integration; where data lives; how requests flow
code:
  - {path/to/compose-or-infra-file}
---

# Architecture

## Components

```
{ASCII diagram: clients → gateways → services → stores}
```

| Component | Role | Tech | Docs |
|---|---|---|---|
| {name} | {what it does} | {stack} | [link](subproject/README.md) |

## How they talk

{Protocols, auth between them, generated clients, which side owns which writes.}

## Shared code

{Packages used by several components and what must stay in them.}

## Data

{Stores, who writes what, migrations, backups.}

## Cross-cutting concerns

{Auth, validation, localisation, images/files, email, observability.}

## Environments

| Env | Where | How deployed | Config |
|---|---|---|---|
| {develop} | {local} | {command} | {file} |
