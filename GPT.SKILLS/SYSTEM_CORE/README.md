# Sistema di Skill per GPT Project

## Overview

Sistema di Skill per GPT Project builds targeted work sessions inside a ChatGPT Project using a small core and a small set of active skills.

It is a session loader, not a permanent skill platform.

The system is designed for:
- ChatGPT Desktop App or web;
- a dedicated Project;
- `GPT.SKILLS.zip` as the core package;
- separate ZIP-based skill packages;
- Python-driven unpack, validation, reading, and mount;
- a small active skill set per session.

It does not use:
- API integration;
- local filesystem orchestration;
- marketplace install;
- auto-install from the internet;
- hooks;
- runtime state files;
- continuous routing.

## Core Shape

The core package extracts to:

```text
GPT.SKILLS/
  SYSTEM_CORE/
  SKILLS/
```

The core uses five logical files:
- `MANIFEST.json`;
- `ENTRY.md`;
- `README.md`;
- `SEMANTICS.md`;
- `OPERATIONAL_RULES.md`.

`MANIFEST.json` controls what is read and in which order.

`ENTRY.md` boots and activates the core.

`SEMANTICS.md` describes the operating model.

`OPERATIONAL_RULES.md` defines lifecycle behavior.

`README.md` provides this descriptive overview.

`SKILLS/` is a physical slot for installed skills.

`SKILLS/README.md` is descriptive only and is not mounted.

## Skill Shape

A standard skill uses:
- `MANIFEST.json`;
- `SKILL.md`.

The skill manifest identifies the package.

`SKILL.md` contains the local capability mounted into the session.

Skills do not redefine global core rules.

A skill present under `SKILLS/` is installed, not active.

Only `SKILL <name> LOAD` makes a skill active in the current session.

## Intended Use

Use the core to create short, controlled, focused sessions.

Install only the skills needed for the current work.

Load only the installed skills that belong in the current session.

Open a new chat when the focus changes enough that the active skill set would become noisy or misleading.
