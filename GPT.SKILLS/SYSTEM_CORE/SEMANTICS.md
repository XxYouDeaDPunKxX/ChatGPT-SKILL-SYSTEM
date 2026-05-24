# SEMANTICS

## Role

This file defines the mental model of the Sistema di Skill per GPT Project.

It does not define command lifecycle, manifest validation, or loader behavior.

## Session-First Model

The session is the operating unit.

The system exists to construct a targeted session with a small, coherent set of active skills.

It is not a permanent skill registry and not a large always-on capability library.

`GPT.SKILLS/` is the physical root of the system after core unpack.

`SYSTEM_CORE/` contains the mounted core.

`SKILLS/` is only a physical deposit for installed skills.

`SKILLS/` is not a semantic registry and does not define the active skill set.

## Core And Skill Split

The core defines:
- bootstrap meaning;
- global lifecycle boundaries;
- command semantics through `OPERATIONAL_RULES.md`;
- validation boundaries;
- limits of the system.

A skill defines:
- what local capability it adds;
- when it is useful;
- what input and output it handles;
- any optional local hints or supporting AI-only files.

A skill must not redefine global core behavior.

## Active Skill Meaning

A loaded skill is semantically active in the current session.

Active means the model has read the mounted skill files and should use them when relevant to the current task.

Active does not mean the skill intercepts requests, runs hooks, watches files, or persists outside the current session.

A skill folder present under `SKILLS/` means the skill is installed physically.

It does not mean the skill is active.

Only `SKILL <name> LOAD` makes an installed skill active.

## Cooperative Composition

Multiple skills can be active in the same session when they support the same work focus.

Their composition is cooperative, not sequential.

The model weighs the active skill pool against the task.

The system should avoid loading skills "just in case" because excess active context degrades focus.

## Mount Meaning

Mount means validated reading of AI-only files declared by a manifest and semantic insertion into the current session context.

Mount does not mean:
- installation into the model;
- runtime binding;
- persistent enforcement;
- automatic routing;
- watcher behavior;
- serialized state.

## Boundary Of Change

When the work focus changes materially, the active session should be closed by opening a new chat and repeating a targeted boot/load cycle.

This keeps the active semantic set small and prevents drift.
