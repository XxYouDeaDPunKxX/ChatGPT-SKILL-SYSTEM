# Skill Adapter

## Purpose

Adapt an external skill into a GPT Project Skill System package.

The adapter is preservation-first.

It does not reorganize a source skill into system-specific folders.

It changes only what is required for:
- path safety;
- ZIP safety;
- GPT Project / mnt compatibility;
- Code Interpreter compatibility;
- manifest identity;
- semantic mount clarity.

## Operating Rule

Produce a candidate package plan and compatibility report before treating an adaptation as accepted.

Do not claim compatibility when a file, dependency, command, runtime assumption, or external mechanism has not been checked.

## Workflow

1. Identify the source.
   - folder path;
   - ZIP path;
   - extracted Project source.

2. Inspect mechanically.
   - Use `scripts/inspect_skill_candidate.py` when file access is available.
   - Check path safety, ZIP entries, file inventory, candidate manifests, likely primary file, scripts, binary files, and external mechanism indicators.

3. Choose loader mode.
   - Use fallback mode only when root `SKILL.md` is the real entry point and `primary_file/load_sequence` can be omitted safely.
   - Use explicit manifest mode when the entry point is nested, when extra mounted files are needed, or when clarity requires explicit `primary_file` and `load_sequence`.

4. Preserve structure.
   - Keep safe original folder names and file names.
   - Do not flatten folders.
   - Do not rename folders into `references/`, `scripts/`, or `assets/` unless required for safety or compatibility.

5. Draft `MANIFEST.json`.
   - `skill_name` must match the command slug, ZIP filename, installed folder, and manifest.
   - `primary_file` must be included in `load_sequence` when explicit mode is used.
   - `load_sequence` must contain only safe relative UTF-8 textual files intended for semantic mount.
   - `support_files`, `tool_files`, and `asset_files` are declarative physical availability fields.

6. Evaluate compatibility.
   - Path-safe files are compatible physically.
   - Textual mounted files must be UTF-8.
   - Tool files must be text and compatible with the available Python environment.
   - Assets may be binary if usable as files from `/mnt`.
   - No `pip install`.
   - No network install.
   - No hook, daemon, watcher, persistent service, local app, external CLI, or proprietary runtime assumption unless explicitly available in the target environment.

7. Report.
   - Return a compatibility rating.
   - List hard blockers.
   - List warnings.
   - List required operator decisions.
   - Provide a manifest draft.
   - State the maximum supported claim.

## Output Shape

Use this structure:

```text
Compatibility: PASS | PASS_WITH_WARNINGS | BLOCKED

Source:
- path:
- shape:

Loader mode:
- fallback | explicit

Manifest draft:
```json
{}
```

Mounted files:
- ...

Physical files:
- support_files:
- tool_files:
- asset_files:

Findings:
- ...

Operator decisions:
- ...

Claim:
- ...
```

## Boundaries

This skill does not modify the core.

This skill does not make a package active.

This skill does not execute tool files automatically.

This skill does not install dependencies.

This skill does not guarantee that every external skill is compatible.

When source structure or runtime assumptions are ambiguous, preserve evidence and ask for a decision instead of inventing a conversion.
