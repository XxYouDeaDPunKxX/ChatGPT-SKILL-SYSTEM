#!/usr/bin/env python3
"""Inspect an external skill candidate for GPT Project Skill System adaptation."""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


TEXT_EXTENSIONS = {
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".rst",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
SCRIPT_EXTENSIONS = {
    ".bat",
    ".bash",
    ".cmd",
    ".cjs",
    ".js",
    ".jsx",
    ".mjs",
    ".ps1",
    ".py",
    ".sh",
    ".ts",
    ".tsx",
    ".zsh",
}
RUNTIME_MARKERS = {
    "pip install": "network/dependency install",
    "npm install": "external package install",
    "pnpm install": "external package install",
    "yarn install": "external package install",
    "docker ": "external runtime",
    "daemon": "persistent service",
    "watcher": "watcher behavior",
    "webhook": "hook behavior",
    "claude": "source assistant runtime wording",
}


def is_safe_relative_path(name: str) -> bool:
    path = PurePosixPath(name)
    if not name or "\\" in name:
        return False
    if name.startswith("/") or path.is_absolute():
        return False
    if re.match(r"^[A-Za-z]:", name):
        return False
    if ".." in path.parts:
        return False
    if "" in name.split("/"):
        return False
    return True


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9_-]+", "-", value.lower()).strip("-_")
    return slug or "adapted-skill"


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def relative_files(root: Path) -> list[str]:
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append(path.relative_to(root).as_posix())
    return files


def inspect_zip(zip_path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str], list[str], bool, str | None]:
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name) / "source"
    root.mkdir()
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        normalized = [name.rstrip("/") for name in names if name.rstrip("/")]
        unsafe = [name for name in normalized if not is_safe_relative_path(name)]

        # Directory entries such as "wrapped/" must not be treated as
        # root-level files.  Wrapper detection is based on real file entries:
        # a single-wrapper ZIP has no root-level files and all files under one
        # top-level directory.
        file_entries = [name for name in names if name.rstrip("/") and not name.endswith("/")]
        normalized_files = [name.rstrip("/") for name in file_entries]
        root_files = [name for name in normalized_files if "/" not in name]
        top_dirs = {name.split("/", 1)[0] for name in normalized_files if "/" in name}
        single_wrapper = bool(normalized_files) and not root_files and len(top_dirs) == 1
        single_wrapper_name = next(iter(top_dirs)) if single_wrapper else None

        if unsafe:
            return root, temp, unsafe, single_wrapper, single_wrapper_name
        archive.extractall(root)
    return root, temp, [], single_wrapper, single_wrapper_name


def load_existing_manifest(root: Path) -> dict | None:
    manifest = root / "MANIFEST.json"
    if not manifest.exists() or manifest.is_dir():
        return None
    try:
        return json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return None


def choose_primary(files: list[str]) -> str | None:
    preferred = [
        "SKILL.md",
        "skill.md",
        "README.md",
        "readme.md",
    ]
    for name in preferred:
        if name in files:
            return name
    skill_named = [name for name in files if PurePosixPath(name).name.lower() == "skill.md"]
    if skill_named:
        return skill_named[0]
    markdown = [name for name in files if PurePosixPath(name).suffix.lower() == ".md"]
    return markdown[0] if markdown else None


def file_category(path: str, root: Path) -> str:
    suffix = PurePosixPath(path).suffix.lower()
    if suffix in SCRIPT_EXTENSIONS:
        return "tool"
    if suffix in TEXT_EXTENSIONS:
        return "support"
    return "asset"


def python_imports(path: Path) -> list[str]:
    text = read_text(path)
    if text is None:
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    return sorted(imports)


def scan_runtime_markers(root: Path, files: list[str]) -> list[dict]:
    findings: list[dict] = []
    for rel in files:
        suffix = PurePosixPath(rel).suffix.lower()
        if suffix not in TEXT_EXTENSIONS:
            continue
        text = read_text(root / rel)
        if text is None:
            continue
        lowered = text.lower()
        for marker, issue in RUNTIME_MARKERS.items():
            if marker in lowered:
                findings.append({"file": rel, "marker": marker, "issue": issue})
    return findings


def stripped_wrapper_paths(files: list[str], wrapper: str | None) -> list[str]:
    if not wrapper:
        return []
    prefix = wrapper.rstrip("/") + "/"
    return [name[len(prefix):] for name in files if name.startswith(prefix) and name != prefix]


def likely_mapping_for_paths(paths: list[str]) -> dict:
    primary = choose_primary(paths)
    support_files: list[str] = []
    tool_files: list[str] = []
    asset_files: list[str] = []
    for rel in paths:
        if rel in {"MANIFEST.json", primary}:
            continue
        category = file_category(rel, Path("."))
        if category == "tool":
            tool_files.append(rel)
        elif category == "support":
            support_files.append(rel)
        else:
            asset_files.append(rel)
    return {
        "primary_file": primary,
        "load_sequence": [primary] if primary else [],
        "support_files": support_files,
        "tool_files": tool_files,
        "asset_files": asset_files,
    }


def manifest_string_array(manifest: dict, field: str, blockers: list[str]) -> list[str] | None:
    if field not in manifest:
        return []
    value = manifest[field]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        blockers.append(f"{field} must be an array of strings.")
        return None
    return value


def validate_declared_file(
    root: Path,
    relative_path: str,
    field: str,
    blockers: list[str],
    require_utf8: bool = False,
    reject_script: bool = False,
) -> None:
    if not is_safe_relative_path(relative_path):
        blockers.append(f"{field} contains unsafe path: {relative_path}")
        return
    path = root.joinpath(*PurePosixPath(relative_path).parts)
    if not path.exists():
        blockers.append(f"{field} declares missing file: {relative_path}")
        return
    if path.is_dir():
        blockers.append(f"{field} declares directory target: {relative_path}")
        return
    if require_utf8 and read_text(path) is None:
        blockers.append(f"{field} declares non-UTF-8 file: {relative_path}")
    if reject_script and PurePosixPath(relative_path).suffix.lower() in SCRIPT_EXTENSIONS:
        blockers.append(f"{field} must not include script/executable file: {relative_path}")


def validate_manifest_draft(root: Path, manifest: dict) -> list[str]:
    blockers: list[str] = []
    primary_present = "primary_file" in manifest
    load_present = "load_sequence" in manifest
    if primary_present != load_present:
        blockers.append("primary_file and load_sequence must either both be present or both be omitted.")
        return blockers

    if not primary_present:
        validate_declared_file(root, "SKILL.md", "fallback primary_file", blockers, require_utf8=True)
        return blockers

    primary_file = manifest.get("primary_file")
    if not isinstance(primary_file, str) or not is_safe_relative_path(primary_file):
        blockers.append(f"primary_file must be a safe relative path: {primary_file!r}")
        return blockers

    load_sequence = manifest_string_array(manifest, "load_sequence", blockers)
    if load_sequence is None:
        return blockers
    if not load_sequence:
        blockers.append("load_sequence must not be empty.")
    if primary_file not in load_sequence:
        blockers.append("primary_file must be included in load_sequence.")

    support_files = manifest_string_array(manifest, "support_files", blockers)
    tool_files = manifest_string_array(manifest, "tool_files", blockers)
    asset_files = manifest_string_array(manifest, "asset_files", blockers)
    if support_files is None or tool_files is None or asset_files is None:
        return blockers

    overlap = set(load_sequence).intersection(support_files)
    if overlap:
        blockers.append("load_sequence and support_files overlap: " + ", ".join(sorted(overlap)))

    for relative_path in load_sequence:
        validate_declared_file(
            root,
            relative_path,
            "load_sequence",
            blockers,
            require_utf8=True,
            reject_script=True,
        )
    for relative_path in support_files:
        validate_declared_file(root, relative_path, "support_files", blockers)
    for relative_path in tool_files:
        validate_declared_file(root, relative_path, "tool_files", blockers, require_utf8=True)
    for relative_path in asset_files:
        validate_declared_file(root, relative_path, "asset_files", blockers)

    return blockers


def build_report(
    input_path: Path,
    source_root: Path,
    unsafe_zip_entries: list[str],
    single_wrapper_zip: bool,
    single_wrapper_name: str | None,
    slug: str | None,
) -> dict:
    files = relative_files(source_root) if not unsafe_zip_entries else []
    wrapper_stripped_files = stripped_wrapper_paths(files, single_wrapper_name) if single_wrapper_zip else []
    existing_manifest = load_existing_manifest(source_root) if not unsafe_zip_entries else None
    primary = None if unsafe_zip_entries else choose_primary(files)
    skill_name = slugify(slug or (existing_manifest or {}).get("skill_name", "") or input_path.stem)

    support_files: list[str] = []
    tool_files: list[str] = []
    asset_files: list[str] = []
    if primary:
        for rel in files:
            if rel in {"MANIFEST.json", primary}:
                continue
            category = file_category(rel, source_root)
            if category == "tool":
                tool_files.append(rel)
            elif category == "support":
                support_files.append(rel)
            else:
                asset_files.append(rel)

    text_failures = []
    if primary and read_text(source_root / primary) is None:
        text_failures.append(primary)

    python_tools = []
    stdlib = getattr(sys, "stdlib_module_names", set())
    for rel in tool_files:
        if PurePosixPath(rel).suffix.lower() == ".py":
            imports = python_imports(source_root / rel)
            third_party = [name for name in imports if name not in stdlib]
            python_tools.append({"file": rel, "imports": imports, "non_stdlib_imports": third_party})

    blockers: list[str] = []
    warnings: list[str] = []
    if single_wrapper_zip:
        blockers.append("ZIP contains a single wrapper directory.")
    if unsafe_zip_entries:
        blockers.append("ZIP contains unsafe entries.")
    if not primary:
        blockers.append("No candidate primary skill file found.")
    if text_failures:
        blockers.append("Candidate mounted file is not UTF-8: " + ", ".join(text_failures))
    for tool in python_tools:
        if tool["non_stdlib_imports"]:
            warnings.append(
                f"{tool['file']} imports non-stdlib modules: "
                + ", ".join(tool["non_stdlib_imports"])
            )

    markers = scan_runtime_markers(source_root, files) if not unsafe_zip_entries else []
    if markers:
        warnings.append("Runtime-specific markers found; inspect marker_findings.")

    existing_explicit = bool(
        existing_manifest
        and ("primary_file" in existing_manifest or "load_sequence" in existing_manifest)
    )
    has_physical_categories = bool(support_files or tool_files or asset_files)
    version = "1.0"
    if existing_manifest and isinstance(existing_manifest.get("version"), str):
        version = existing_manifest["version"]

    detected_manifest = None
    if primary == "SKILL.md" and not has_physical_categories:
        loader_mode = "fallback"
        detected_manifest = {"skill_name": skill_name, "version": version}
    else:
        loader_mode = "explicit"
        detected_manifest = {
            "skill_name": skill_name,
            "version": version,
            "primary_file": primary,
            "load_sequence": [primary] if primary else [],
            "support_files": support_files,
            "tool_files": tool_files,
            "asset_files": asset_files,
        }

    draft_blockers = []
    if not unsafe_zip_entries and not single_wrapper_zip:
        source_manifest_blockers = []
        if existing_explicit:
            source_manifest = {
                "skill_name": skill_name,
                "version": version,
                "primary_file": existing_manifest.get("primary_file"),
                "load_sequence": existing_manifest.get("load_sequence"),
                "support_files": existing_manifest.get("support_files", []),
                "tool_files": existing_manifest.get("tool_files", []),
                "asset_files": existing_manifest.get("asset_files", []),
            }
            source_manifest_blockers = validate_manifest_draft(source_root, source_manifest)
        if existing_explicit and source_manifest_blockers:
            blockers.append("Existing explicit manifest is invalid and was not accepted for reuse.")
            blockers.extend(source_manifest_blockers)
            rejected_source_manifest = existing_manifest
            manifest_draft = None
        elif existing_explicit:
            manifest_draft = {
                "skill_name": skill_name,
                "version": version,
                "primary_file": existing_manifest.get("primary_file"),
                "load_sequence": existing_manifest.get("load_sequence"),
                "support_files": existing_manifest.get("support_files", []),
                "tool_files": existing_manifest.get("tool_files", []),
                "asset_files": existing_manifest.get("asset_files", []),
            }
            rejected_source_manifest = None
        else:
            manifest_draft = detected_manifest
            rejected_source_manifest = None

        if manifest_draft is not None:
            draft_blockers = validate_manifest_draft(source_root, manifest_draft)
    else:
        manifest_draft = None
        rejected_source_manifest = existing_manifest if existing_explicit else None

    blockers.extend(draft_blockers)

    if draft_blockers:
        manifest_draft = None

    if blockers:
        compatibility = "BLOCKED"
    elif warnings:
        compatibility = "PASS_WITH_WARNINGS"
    else:
        compatibility = "PASS"

    adaptation_hint = None
    likely_mapping_after_unwrap = None
    if single_wrapper_zip:
        adaptation_hint = {
            "action": "unwrap_single_wrapper",
            "wrapper": single_wrapper_name,
            "preserve_internal_paths": True,
            "next_step": "remove the wrapper directory, add MANIFEST.json at ZIP root, then re-run inspection",
        }
        likely_mapping_after_unwrap = likely_mapping_for_paths(wrapper_stripped_files)

    return {
        "compatibility": compatibility,
        "source": str(input_path),
        "loader_mode": loader_mode,
        "files": files,
        "unsafe_zip_entries": unsafe_zip_entries,
        "single_wrapper_zip": single_wrapper_zip,
        "single_wrapper_name": single_wrapper_name,
        "adaptation_hint": adaptation_hint,
        "likely_mapping_after_unwrap": likely_mapping_after_unwrap,
        "existing_manifest": existing_manifest,
        "rejected_source_manifest": rejected_source_manifest,
        "manifest_draft": manifest_draft,
        "support_files": support_files,
        "tool_files": tool_files,
        "asset_files": asset_files,
        "python_tools": python_tools,
        "marker_findings": markers,
        "blockers": blockers,
        "warnings": warnings,
        "claim": "candidate inspected for GPT Project Skill System adaptation; operator review still required",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to external skill folder or ZIP")
    parser.add_argument("--slug", help="Override skill_name slug")
    parser.add_argument("--output", help="Write JSON report to this path")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"input not found: {input_path}")

    temp: tempfile.TemporaryDirectory[str] | None = None
    unsafe_zip_entries: list[str] = []
    single_wrapper_zip = False
    single_wrapper_name = None
    if input_path.is_file():
        if input_path.suffix.lower() != ".zip":
            raise SystemExit("file input must be a ZIP")
        source_root, temp, unsafe_zip_entries, single_wrapper_zip, single_wrapper_name = inspect_zip(input_path)
    else:
        source_root = input_path

    try:
        report = build_report(
            input_path,
            source_root,
            unsafe_zip_entries,
            single_wrapper_zip,
            single_wrapper_name,
            args.slug,
        )
        text = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(text)
    finally:
        if temp is not None:
            temp.cleanup()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
