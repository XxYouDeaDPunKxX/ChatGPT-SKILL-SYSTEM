# Adapting a Skill

## Purpose

This guide explains how to adapt an external text-based skill into a package compatible with the GPT Project Skill System.

It is repository documentation only.

It is not part of `GPT.SKILLS.zip`.

It is not mounted by the runtime core.

It does not define loader behavior.

## Compatible Skill Shapes

For full package details, see `docs/SKILL_PACKAGE_FORMAT.md`.

### Fallback Skill

A fallback skill package is a flat ZIP containing:

```text
MANIFEST.json
SKILL.md
```

The ZIP must not contain a wrapper directory.

Valid:

```text
summarizer.zip
  MANIFEST.json
  SKILL.md
```

Invalid:

```text
summarizer.zip
  summarizer/
    MANIFEST.json
    SKILL.md
```

Fallback mode is appropriate only when the root `SKILL.md` is the skill entry point.

### Explicit Manifest Skill

An explicit manifest skill declares `primary_file` and `load_sequence`.

It can preserve safe relative folders from the original source:

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

The format does not require specific folder names.

Preserve the original structure whenever possible.

Do not rename, move, flatten, or normalize folders unless required for:
- path safety;
- ZIP safety;
- GPT Project / mnt compatibility;
- Code Interpreter compatibility;
- manifest identity;
- semantic mount clarity.

## Name Identity

The skill name must match across:
- command slug;
- ZIP filename;
- installed folder;
- `skill_name` in `MANIFEST.json`.

Example:

```text
SKILL summarizer UNPACK
summarizer.zip
/mnt/data/GPT.SKILLS/SKILLS/summarizer/
```

```json
{
  "skill_name": "summarizer",
  "version": "1.0"
}
```

## Slug Rule

Use a simple slug for `skill_name`.

Allowed:
- lowercase letters;
- digits;
- underscore;
- hyphen.

Pattern:

```text
^[a-z0-9_-]+$
```

Invalid:
- empty name;
- spaces;
- uppercase letters;
- dot;
- slash;
- backslash;
- `..`.

Examples:

```text
summarizer      valid
legal-review    valid
a_b-1           valid
my skill        invalid
Summarizer      invalid
skill.name      invalid
../x            invalid
x/y             invalid
```

## Fallback Manifest

Use the fallback manifest when the skill only needs root `SKILL.md`.

```json
{
  "skill_name": "summarizer",
  "version": "1.0"
}
```

With this shape, the loader uses fallback mode:

```json
{
  "primary_file": "SKILL.md",
  "load_sequence": ["SKILL.md"]
}
```

The fallback is implicit. Do not add it unless you need to be explicit.

Root `SKILL.md` is required only in fallback mode.

If `primary_file` and `load_sequence` are explicit:
- `primary_file` may be any safe relative UTF-8 textual file;
- `primary_file` must be included in `load_sequence`;
- root `SKILL.md` is not required.

Providing only one of `primary_file` or `load_sequence` is invalid.

## Explicit Manifest

Use an explicit manifest when the skill needs a declared `primary_file`, a declared `load_sequence`, extra files, or lightweight descriptive metadata.

```json
{
  "skill_name": "summarizer",
  "version": "1.0",
  "primary_file": "SKILL.md",
  "load_sequence": ["SKILL.md"],
  "support_files": ["docs/columns.md"],
  "tool_files": ["tools/profile_csv.py"],
  "asset_files": ["templates/template.csv"],
  "capabilities": ["summarization"],
  "runtime_hints": {
    "uses_python": true
  }
}
```

Keep `runtime_hints` lightweight.

Do not turn `runtime_hints` into a dependency manager.

Do not use it for behavior that the loader cannot validate mechanically.

If you add extra mounted AI-only files:
- declare mounted files in `load_sequence`;
- keep `primary_file` inside `load_sequence`;
- use only AI-only textual files;
- use safe relative paths.

Extra files can exist physically in the ZIP, but only files declared in `load_sequence` are mounted.

Use `support_files` for supplemental files that should be available when needed but not mounted automatically.

Use `tool_files` for safe relative scripts or tools; they are never mounted or run automatically.

Use `asset_files` for safe relative data, templates, media, or other physical files; they are never mounted automatically.

If present, `support_files`, `tool_files`, and `asset_files` must be arrays of strings.

Every entry in those fields must be a safe relative path and must exist in the package.

Do not overlap `load_sequence` and `support_files`.

Tool files may use only Python standard library or packages already available in the current GPT Python environment.

No `pip install`.

No network install.

## Requirements And Dependencies

Put real requirements in the body of `SKILL.md` as text.

Example:

```markdown
## Requirements

- Needs access to uploaded source files.
- Uses only Project-visible files.
- No internet required.
```

This keeps dependency claims readable without forcing the loader to validate capabilities it cannot guarantee.

## Preserving Existing Skill Text

When adapting an external skill, preserve the original body whenever possible.

Preserve the original folder structure whenever possible.

Preferred adaptation:
- create `MANIFEST.json`;
- keep the existing skill text in `SKILL.md`;
- keep safe original folders and file names;
- add a short `## Requirements` section only if needed;
- do not add global system rules to the skill.

Avoid:
- rewriting the skill into a mini-framework;
- reorganizing folders into system-specific taxonomy;
- adding bootstrap rules;
- adding loader lifecycle rules;
- duplicating core behavior;
- adding marketplace or auto-install assumptions.

## Packaging Steps

1. Choose a slug.
2. Create a package folder with `MANIFEST.json` and the declared primary skill file.
   For fallback mode, the primary file must be root `SKILL.md`.
   For explicit manifest mode, the primary file may be any safe relative UTF-8 textual file.
3. Verify `skill_name` equals the slug.
4. Verify the ZIP filename is `<skill_name>.zip`.
5. Create a ZIP with `MANIFEST.json` at root, no wrapper directory, and preserved safe internal paths.
6. Confirm there is no wrapper directory inside the ZIP.
7. Load through the normal command lifecycle:

```text
SKILL <name> UNPACK
SKILL <name> LOAD
```

## Valid Package Example

```text
summarizer.zip
  MANIFEST.json
  SKILL.md
```

`MANIFEST.json`:

```json
{
  "skill_name": "summarizer",
  "version": "1.0"
}
```

`SKILL.md`:

```markdown
# Summarizer

Summarize long text while preserving key decisions, constraints, and unresolved questions.

## Requirements

- Needs access to the source text.
- No internet required.
```

## Invalid Package Examples

Wrapper directory:

```text
summarizer.zip
  summarizer/
    MANIFEST.json
    SKILL.md
```

Name mismatch:

```text
SKILL summarizer UNPACK
reviewer.zip
```

Manifest mismatch:

```json
{
  "skill_name": "reviewer",
  "version": "1.0"
}
```

Invalid slug:

```text
SKILL My Skill UNPACK
```

## Checklist

- `MANIFEST.json` exists.
- Fallback mode: root `SKILL.md` exists.
- Explicit manifest mode: declared `primary_file` exists and is included in `load_sequence`.
- ZIP is flat.
- ZIP filename is `<skill_name>.zip`.
- Command slug equals `skill_name`.
- Installed folder will be `/mnt/data/GPT.SKILLS/SKILLS/<skill_name>/`.
- `skill_name` follows `^[a-z0-9_-]+$`.
- `version` is a non-empty string.
- `MANIFEST.json` is valid UTF-8 JSON.
- Fallback mode: `SKILL.md` is UTF-8 text/Markdown.
- Explicit manifest mode: declared `primary_file` is UTF-8 text/Markdown.
- Declared load files are AI-only textual files.
- Extra mounted files are declared in `load_sequence`.
- Extra mounted files are AI-only textual files.
- Internal paths are safe relative paths.
- Internal paths do not contain `..`, backslashes, drive letters, or empty segments.
- `support_files` does not overlap with `load_sequence`.
- `tool_files` are not mounted and not run automatically.
- `asset_files` are not mounted automatically.
- No `pip install` or network install is required.
- Requirements are in `SKILL.md`, not a strong manifest schema.
- The skill does not redefine core rules.
