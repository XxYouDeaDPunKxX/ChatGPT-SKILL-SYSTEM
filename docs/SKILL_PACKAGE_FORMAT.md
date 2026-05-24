# Skill Package Format

## Purpose

This document defines the supported skill package shapes for the GPT Project Skill System.

It is repository documentation.

Runtime rules live in `GPT.SKILLS/SYSTEM_CORE/OPERATIONAL_RULES.md`.

## Fallback Skill

A fallback skill package is a flat ZIP:

```text
summarizer.zip
  MANIFEST.json
  SKILL.md
```

Fallback `MANIFEST.json`:

```json
{
  "skill_name": "summarizer",
  "version": "1.0"
}
```

If `primary_file` and `load_sequence` are omitted, the loader uses fallback mode:

```json
{
  "primary_file": "SKILL.md",
  "load_sequence": ["SKILL.md"]
}
```

Root `SKILL.md` is required only in fallback mode.

If `primary_file` and `load_sequence` are explicit:
- `primary_file` may be any safe relative UTF-8 textual file;
- `primary_file` must be included in `load_sequence`;
- root `SKILL.md` is not required.

Providing only one of `primary_file` or `load_sequence` is invalid.

## Explicit Manifest Skill

An explicit manifest skill declares `primary_file` and `load_sequence`.

It may preserve safe relative internal folders from the original source:

```text
csv-profiler.zip
  MANIFEST.json
  SKILL.md
  docs/
    columns.md
  tools/
    profile_csv.py
  templates/
    template.csv
```

The package format does not require specific folder names.

Folders are preserved unless safety or compatibility requires a change.

## Manifest Example

```json
{
  "skill_name": "csv-profiler",
  "version": "1.0",
  "primary_file": "SKILL.md",
  "load_sequence": [
    "SKILL.md"
  ],
  "support_files": [
    "docs/columns.md"
  ],
  "tool_files": [
    "tools/profile_csv.py"
  ],
  "asset_files": [
    "templates/template.csv"
  ],
  "capabilities": ["csv analysis"],
  "runtime_hints": {
    "uses_python": true
  }
}
```

## Mount Semantics

`load_sequence` is the only automatic semantic mount list.

Files in `load_sequence` are read into the active skill context during `SKILL <name> LOAD`.

Files outside `load_sequence` are physically available after unpack, but they are not active context automatically.

## File Categories

`load_sequence`:
- automatic semantic mount;
- AI-only textual files only;
- may include `SKILL.md`;
- may include safe relative UTF-8 textual files, including nested files;
- must include `primary_file`;
- every entry must exist and be a file target;
- must not include scripts intended for execution or binary assets.

`support_files`:
- supplemental reference files;
- consulted only when needed;
- category, not folder policy;
- if present, must be an array of strings;
- every entry must be a safe relative path;
- every declared file must exist and be a file target;
- not mounted automatically;
- must not overlap with `load_sequence`.

`tool_files`:
- script files physically available to the Python environment;
- safe relative scripts or tools compatible with the current Python environment;
- if present, must be an array of strings;
- every entry must be a safe relative path;
- every declared file must exist, be a file target, and be UTF-8 text;
- never mounted automatically;
- never run automatically.

`asset_files`:
- data or template files physically available to the task;
- safe relative physical files;
- if present, must be an array of strings;
- every entry must be a safe relative path;
- every declared file must exist and be a file target;
- not mounted automatically;
- may be non-textual when the environment can use them as files.

`runtime_hints`:
- descriptive metadata only;
- not a control plane;
- not dependency management.

## Path Policy

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

Disallowed:
- absolute paths;
- `..`;
- backslash paths;
- drive letters;
- empty path segments;
- wrapper directory at ZIP root;
- directories in `load_sequence`;
- binary assets in `load_sequence`;
- scripts intended for execution in `load_sequence`;
- unavailable external resources in `load_sequence`.

## Overlap Rules

`load_sequence` and `support_files` must not overlap.

If a reference file should always be active, put it in `load_sequence`.

If a reference file should be available only when needed, put it in `support_files`.

Overlap between `load_sequence` and `support_files` is hard fail.

## Tool File Rules

Tool files are never executed automatically.

Tool files may use only:
- Python standard library;
- packages already available in the current GPT Python environment.

No `pip install`.

No network install.

If a dependency is missing, tool execution must degrade or fail with a clear warning.

The skill should provide a non-script fallback when possible.

## Packaging Rules

The ZIP must be flat at root.

Flat means:
- `MANIFEST.json` is at ZIP root;
- no single wrapper folder surrounds the package;
- internal folders are allowed when path-safe.

Valid:

```text
csv-profiler.zip
  MANIFEST.json
  SKILL.md
  docs/
  tools/
  templates/
```

Invalid:

```text
csv-profiler.zip
  csv-profiler/
    MANIFEST.json
    SKILL.md
```

Wrapper directory is hard fail.

The ZIP filename, command slug, installed folder, and `skill_name` must match.
