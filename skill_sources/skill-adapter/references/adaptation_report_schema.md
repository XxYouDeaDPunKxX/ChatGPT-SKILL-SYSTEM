# Adaptation Report Schema

## Purpose

Use this schema when reporting an external skill adaptation.

The report is evidence for operator review.

It is not proof of general compatibility.

## Required Sections

```text
Compatibility: PASS | PASS_WITH_WARNINGS | BLOCKED

Source:
- input:
- inspected shape:
- existing manifest:

Loader mode:
- fallback | explicit
- reason:

Manifest draft:
- skill_name:
- version:
- primary_file:
- load_sequence:
- support_files:
- tool_files:
- asset_files:

Compatibility checks:
- path safety:
- ZIP safety:
- UTF-8 mounted files:
- physical file availability:
- Python tool compatibility:
- external mechanisms:
- dependency assumptions:

Findings:
- severity:
- file:
- issue:
- fix:

Operator decisions:
- ...

Maximum supported claim:
- ...
```

## Ratings

`PASS` means:
- no hard blockers found;
- package can be built under the current rules;
- remaining assumptions are explicit.

`PASS_WITH_WARNINGS` means:
- package can be built;
- some files or behaviors require operator review or task-time caution.

`BLOCKED` means:
- a hard blocker prevents a valid package candidate.

## Hard Blockers

Hard blockers include:
- unsafe paths;
- ZIP entries with backslashes;
- missing declared files;
- invalid manifest identity;
- mounted file not readable as UTF-8;
- script or binary file in `load_sequence`;
- required dependency unavailable in the GPT Python environment;
- required hook, daemon, watcher, external CLI, local app, or network install.

## Warning Conditions

Warning conditions include:
- unknown optional files preserved physically;
- scripts with imports not confirmed in the target environment;
- binary assets that need task-time handling;
- platform-specific wording in the source skill;
- source instructions that assume another assistant runtime.
