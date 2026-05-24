# OPERATIONAL_RULES

## Role

This file defines execution rules for the Sistema di Skill per GPT Project core.

It is the source of command lifecycle and validation behavior.

## Commands

## Command Target Boundaries

Each lifecycle command may operate only on its declared target.

`SKILL CORE UNPACK` targets only `GPT.SKILLS.zip`.

`SKILL CORE UNPACK` must not unpack, inspect, validate, load, compile, or activate any skill package.

Skill ZIP files present among Project sources are inert until an explicit `SKILL <name> UNPACK`.

Presence in Project sources does not imply install, validation, load, activation, mount, pre-scan, or tool availability.

`SKILL <name> UNPACK` targets only `<name>.zip`.

`SKILL <name> LOAD` targets only the installed skill at `/mnt/data/GPT.SKILLS/SKILLS/<name>/`.

The runtime must not pre-scan, pre-validate, compile, inspect, or infer capability from skill packages that were not named by an explicit lifecycle command.

## Package ZIP Entry Policy

Package ZIP entries must use POSIX `/` path separators.

Package ZIP entries must not contain `\`.

The runtime must fail fast if a core or skill package contains ZIP entries with `\`.

The runtime must not silently normalize invalid ZIP entries.

### SKILL CORE UNPACK

Boots the core from `GPT.SKILLS.zip`.

Behavior:
- removes `/mnt/data/GPT.SKILLS/` before extraction;
- removes any legacy `/mnt/data/sistema_madre/` before extraction;
- extracts `GPT.SKILLS.zip` into `/mnt/data/GPT.SKILLS/`;
- does not fall back to `/mnt/data/sistema_madre/`;
- validates `/mnt/data/GPT.SKILLS/SYSTEM_CORE/MANIFEST.json`;
- validates and mounts files declared in the manifest;
- activates the core for the current session.

Hard fail if core unpack produces any root other than `/mnt/data/GPT.SKILLS/`.

Rerunning this command in the same chat resets the active semantic state.

Previously loaded skills are no longer considered active after core unpack.

### SKILL <name> UNPACK

Installs a skill package physically into the skill directory.

Behavior:
- validates `<name>` as a skill slug;
- verifies the skill ZIP filename is `<name>.zip`;
- verifies the skill ZIP has root `MANIFEST.json` and no single wrapper directory;
- verifies `skill_name` in the skill manifest equals `<name>`;
- extracts the skill ZIP into `/mnt/data/GPT.SKILLS/SKILLS/<name>/`;
- overwrites the previous extracted copy for the same skill;
- validates the skill package enough to support later load.

The skill ZIP is expected to be flat at root.

Flat at root means:
- `MANIFEST.json` is at ZIP root;
- no single wrapper directory surrounds the package;
- safe internal folders are allowed.

The ZIP name, command slug, installed folder, and `skill_name` in the skill manifest must match.

`<name>` must be a simple slug:
- only `[a-z0-9_-]`;
- not empty;
- no spaces;
- no `.`;
- no `/`;
- no `\`;
- no `..`.

Hard fail if:
- `<name>` violates the slug rule;
- the ZIP filename is not `<name>.zip`;
- `skill_name` does not equal `<name>`;
- the install path is not `/mnt/data/GPT.SKILLS/SKILLS/<name>/`;
- the ZIP contains a single wrapper directory around the package.

Unpack installs the skill physically. It does not activate the skill semantically.

### SKILL <name> LOAD

Mounts a skill already installed in `/mnt/data/GPT.SKILLS/SKILLS/<name>/`.

Behavior:
- does not auto-unpack;
- fails if the skill has not been unpacked into the expected path;
- reads the skill manifest;
- reads the skill load sequence or fallback primary file;
- makes the skill semantically active in the current session.

Reloading the same skill performs a full semantic reload.

A skill folder present under `/mnt/data/GPT.SKILLS/SKILLS/` is installed, not active.

Only `SKILL <name> LOAD` makes that skill active in the current session.

## Manifest Validation

The core manifest requires:
- `system_name`;
- `version`;
- `primary_file`;
- `load_sequence`;
- `optional_load_sequence`.

For core version `0.6`:
- `system_name` must be exactly `gpt_project_skill_system`;
- `version` must be exactly `"0.6"`;
- `primary_file` must be a string;
- `load_sequence` must be a non-empty array of strings;
- `optional_load_sequence` must be an array of strings;
- `primary_file` must be included in `load_sequence`.

Manifest invalidity includes:
- missing required field;
- invalid field type;
- invalid `system_name`;
- invalid `version`;
- duplicate entries inside `load_sequence`;
- duplicate entries inside `optional_load_sequence`;
- overlap between `load_sequence` and `optional_load_sequence`;
- absolute path;
- path containing `..`;
- path outside `SYSTEM_CORE/`;
- path using a subdirectory;
- unsupported mounted file extension.

Manifest invalidity causes hard fail.

## Path Policy

All declared core paths are relative to `SYSTEM_CORE/`.

In core version `0.6`, mounted paths must be direct filenames.

Allowed mounted extensions for the core are:
- `.md`;
- `.json`.

Disallowed:
- absolute paths;
- `..`;
- references outside `SYSTEM_CORE/`;
- subdirectories in mounted paths.

Files not declared in the manifest may be unpacked but are not mounted.

`SKILLS/README.md` is not mountable and must not appear in `SYSTEM_CORE/MANIFEST.json`.

`SKILLS/README.md` must not be used as a list of active skills.

## Mechanical Validation

Python must guarantee mechanical validation:
- parse manifest JSON;
- validate fields and types;
- validate `system_name`;
- validate `version`;
- detect duplicate entries inside each load list;
- detect overlap between required and optional lists;
- enforce path policy;
- enforce manifest invalidity;
- inspect extracted-tree load invalidity;
- inspect extracted-tree load degradation;
- confirm required file presence;
- confirm UTF-8 readability of required files;
- probe UTF-8 readability of present optional files, with degradable outcome;
- enforce mounted file extensions;
- distinguish file targets from directory targets.

## Semantic Review

Semantic review is external to the runtime core.

It checks:
- file role separation;
- no lifecycle rules in `SEMANTICS.md`;
- no operative obligations in `README.md`;
- no hook, binding, watcher, routing, or persistent enforcement claims;
- no global core rules inside skills;
- no alternate mount order outside `MANIFEST.json`;
- no contradiction between core files and manifest order.

Semantic review is not reliable Python hard validation.

## Load Invalidity From Extracted Tree

After unpack, load is invalid if:
- a required file is missing;
- a required path is a directory;
- a required file is not readable as UTF-8;
- a present optional path is a directory.

These conditions are found by inspecting the extracted tree, not by parsing JSON alone.

Load invalidity causes hard fail.

## Load Degradation From Extracted Tree

After unpack, load is degraded if:
- an optional file is missing;
- an optional file is present but not readable as UTF-8.

These conditions do not invalidate load when the manifest is valid.

They produce a technical warning and the involved optional file is not mounted.

## Hard Load

Hard fail if:
- `MANIFEST.json` is missing;
- `MANIFEST.json` is not valid JSON;
- the manifest is invalid;
- `primary_file` is missing;
- any file in `load_sequence` is missing;
- any required file is not AI-only textual;
- any required path is a directory;
- any present optional path is a directory.

The following are semantic invalidities, not mechanical hard fail:
- another core file declares alternate mount order;
- `README.md` contains operational rules;
- `SEMANTICS.md` contains lifecycle commands;
- a core file claims hook, binding, watcher, routing, or persistent enforcement behavior.

## Degraded Load

Degraded load is allowed only for files in `optional_load_sequence`, and only after the manifest is valid.

Degraded load applies when:
- an optional file is missing;
- an optional file is present but not readable as UTF-8.

Degraded load behavior:
- continue;
- do not mount the optional file involved;
- emit a concise technical warning;
- do not represent the optional file as active.

Never degradable:
- `MANIFEST.json`;
- `primary_file`;
- any file in `load_sequence`;
- any invalid manifest path;
- directory target.

## Skill Manifest Fallback

A standard skill manifest requires:
- `skill_name`;
- `version`.

`skill_name` must match the command slug `<name>`, the ZIP filename `<name>.zip`, and the installed folder `/mnt/data/GPT.SKILLS/SKILLS/<name>/`.

If a skill manifest omits both `primary_file` and `load_sequence`, the loader uses fallback mode:
- `primary_file`: `SKILL.md`;
- `load_sequence`: `["SKILL.md"]`.

This fallback applies to skills, not to the core.

Core `load_sequence` is required.

Root `SKILL.md` is required only in fallback mode.

If `primary_file` and `load_sequence` are explicit:
- `primary_file` may be any safe relative UTF-8 textual file;
- `primary_file` must be included in `load_sequence`;
- root `SKILL.md` is not required.

Providing only one of `primary_file` or `load_sequence` is invalid.

## Skill Manifest Optional Fields

Allowed optional fields:
- `primary_file`;
- `load_sequence`;
- `support_files`;
- `tool_files`;
- `asset_files`;
- `capabilities`;
- `runtime_hints`.

`primary_file` and `load_sequence` affect skill load behavior.

`support_files` declares supplemental reference files available after unpack.

`tool_files` declares script files available after unpack.

`asset_files` declares data or template files available after unpack.

If present:
- `support_files` must be an array of strings;
- `tool_files` must be an array of strings;
- `asset_files` must be an array of strings.

Every entry in these fields must be a safe relative path.

Every declared file in these fields must exist after unpack and must be a file target, not a directory.

`capabilities` is lightweight descriptive metadata.

If present, `capabilities` should be an array of strings.

`runtime_hints` is lightweight descriptive metadata.

If present, `runtime_hints` should be a JSON object.

`capabilities` and `runtime_hints` do not create:
- dependency management;
- authorization;
- routing;
- validation guarantees;
- automatic tool access.

Invalid optional metadata type produces a warning and is ignored.

It does not hard fail load because it does not affect mount behavior.

Unknown manifest fields are ignored or warned.

Unknown manifest fields are not mounted.

## Skill Package Path Policy

Core path policy and skill path policy are different.

Core mounted paths remain direct filenames only.

Skill packages may preserve original safe relative internal paths.

Safe relative paths:
- are not absolute;
- do not contain `..`;
- do not use backslash paths;
- do not contain empty path segments;
- do not contain drive letters;
- do not rely on traversal;
- do not use a wrapper directory as the sole ZIP root.

`load_sequence` remains the only automatic semantic mount list.

Files in `load_sequence` must be AI-only textual files.

`load_sequence` may include `SKILL.md` and any safe relative UTF-8 textual file.

Every file in `load_sequence` must exist after unpack and must be a file target, not a directory.

`load_sequence` must not include:
- directories;
- binary assets;
- scripts intended for execution;
- unavailable external resources.

`support_files` declares supplemental reference files that are physically available after unpack and consulted only when needed.

`support_files` may point to any safe relative file.

`support_files` is not mounted automatically.

`tool_files` declares safe relative scripts or tools compatible with the current GPT Python environment.

`tool_files` are physically available after unpack.

`tool_files` are never mounted automatically and never run automatically.

`asset_files` declares safe relative data, templates, media, or other files physically usable from `/mnt`.

`asset_files` are physically available after unpack and are never mounted automatically.

`asset_files` may be non-textual when used as files by the environment.

Overlap between `load_sequence` and `support_files` is hard fail.

Tool files may use only:
- Python standard library;
- packages already available in the current GPT Python environment.

No `pip install`.

No network install.

If a dependency is missing, tool execution degrades or fails with a warning.

The skill should provide a non-script fallback when possible.

## Runtime Limits

The system does not provide:
- hooks;
- watcher behavior;
- persistent runtime state;
- automatic routing;
- install into the model;
- marketplace behavior;
- internet auto-install.

The active semantic set exists only in the current session.
