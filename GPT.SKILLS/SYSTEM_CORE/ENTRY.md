# ENTRY

## Role

This file is the bootstrap and activation entry point for the Sistema di Skill per GPT Project core.

It activates the core for the current GPT Project session after the core package has been unpacked and validated.

## Activation Contract

The core is active only inside the current session.

Activation means:
- the files declared in `MANIFEST.json` have been read in manifest order;
- required files have passed mechanical validation;
- optional files, if declared, have either mounted successfully or produced degraded load warnings;
- the model treats the mounted files as the active semantic perimeter for the session.

Activation does not mean:
- installation into the model;
- hook execution;
- runtime binding;
- watcher behavior;
- persistent enforcement;
- routing outside the current session;
- serialized runtime state.

## Bootstrap Order

The reading order is defined only by `MANIFEST.json`.

`ENTRY.md` is the primary file, but it does not redefine the manifest order.

The core runtime files are:
- `ENTRY.md`;
- `README.md`;
- `SEMANTICS.md`;
- `OPERATIONAL_RULES.md`.

## Session Boundary

The active unit is the session, not a permanent library state.

When the work focus changes materially, the correct move is a new GPT Project chat and a fresh targeted boot/load cycle.

Rerunning core unpack in the same session resets the active core state and clears previously loaded skills from the active semantic set.

## Command Authority

Lifecycle commands and execution rules are governed by `OPERATIONAL_RULES.md`.

The model must not infer command behavior from this file when `OPERATIONAL_RULES.md` defines it more specifically.
