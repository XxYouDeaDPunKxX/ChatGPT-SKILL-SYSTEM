#!/usr/bin/env python3
"""Build GPT Project Skill System runtime packages with POSIX ZIP entries."""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPO_ROOT / "GPT.SKILLS"
SKILL_SOURCES = REPO_ROOT / "skill_sources"
DIST = REPO_ROOT / "dist"
SKILL_DIST = DIST / "skills"
CORE_MOUNT_EXTENSIONS = {".md", ".json"}
SCRIPT_EXTENSIONS = {
    ".bat",
    ".bash",
    ".cmd",
    ".cjs",
    ".exe",
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


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


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


def require_string_array(manifest: dict, field: str, required: bool = False) -> list[str]:
    if field not in manifest:
        if required:
            fail(f"missing required manifest field: {field}")
        return []
    value = manifest[field]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        fail(f"{field} must be an array of strings")
    if len(value) != len(set(value)):
        fail(f"{field} contains duplicate entries")
    for item in value:
        if not is_safe_relative_path(item):
            fail(f"{field} contains unsafe path: {item}")
    return value


def iter_package_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(source.rglob("*")):
        if path.is_dir():
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.suffix.lower() == ".zip":
            fail(f"nested zip source is not allowed: {path.relative_to(REPO_ROOT)}")
        files.append(path)
    return files


def write_zip(source: Path, destination: Path) -> None:
    if not source.is_dir():
        fail(f"source directory missing: {source}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()

    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in iter_package_files(source):
            arcname = path.relative_to(source).as_posix()
            if "\\" in arcname:
                fail(f"invalid ZIP entry separator while building {destination.name}: {arcname}")
            archive.write(path, arcname)

    validate_no_backslash_entries(destination)


def validate_entry_names(names: list[str], package_label: str) -> None:
    bad = [name for name in names if "\\" in name]
    if bad:
        fail(
            f"invalid ZIP entries in {package_label}; "
            "entries must use POSIX '/' separators:\n" + "\n".join(bad)
        )

    unsafe = [name for name in names if not is_safe_relative_path(name)]

    if unsafe:
        fail(
            f"invalid ZIP entries in {package_label}; entries must be safe relative paths:\n"
            + "\n".join(unsafe)
        )


def validate_no_backslash_entries(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()

    validate_entry_names(names, str(zip_path.relative_to(REPO_ROOT)))
    return names


def require_core_string_array(manifest: dict, field: str) -> list[str]:
    if field not in manifest:
        fail(f"core manifest missing required field: {field}")
    value = manifest[field]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        fail(f"core manifest {field} must be an array of strings")
    if len(value) != len(set(value)):
        fail(f"core manifest {field} contains duplicate entries")
    return value


def validate_core_mount_path(relative_path: str, field: str) -> None:
    if not is_safe_relative_path(relative_path):
        fail(f"core manifest {field} contains unsafe path: {relative_path}")
    path = PurePosixPath(relative_path)
    if len(path.parts) != 1:
        fail(f"core manifest {field} must use direct filenames only: {relative_path}")
    if path.suffix.lower() not in CORE_MOUNT_EXTENSIONS:
        fail(f"core manifest {field} uses unsupported extension: {relative_path}")


def validate_core_manifest(manifest: dict, names: list[str], read_entry) -> None:
    required_fields = {
        "system_name",
        "version",
        "primary_file",
        "load_sequence",
        "optional_load_sequence",
    }
    missing_fields = sorted(required_fields - set(manifest))
    if missing_fields:
        fail("core manifest missing required fields: " + ", ".join(missing_fields))

    if manifest.get("system_name") != "gpt_project_skill_system":
        fail("core manifest system_name must be gpt_project_skill_system")
    if manifest.get("version") != "0.6":
        fail("core manifest version must be 0.6")

    primary_file = manifest.get("primary_file")
    if not isinstance(primary_file, str):
        fail("core manifest primary_file must be a string")

    load_sequence = require_core_string_array(manifest, "load_sequence")
    optional_load_sequence = require_core_string_array(manifest, "optional_load_sequence")
    if not load_sequence:
        fail("core manifest load_sequence must not be empty")
    if primary_file not in load_sequence:
        fail("core manifest primary_file must be included in load_sequence")

    overlap = set(load_sequence).intersection(optional_load_sequence)
    if overlap:
        fail("core manifest load_sequence/optional_load_sequence overlap: " + ", ".join(sorted(overlap)))

    for relative_path in [primary_file, *load_sequence]:
        validate_core_mount_path(relative_path, "load_sequence")
    for relative_path in optional_load_sequence:
        validate_core_mount_path(relative_path, "optional_load_sequence")

    name_set = set(names)
    for relative_path in load_sequence:
        entry = f"SYSTEM_CORE/{relative_path}"
        if entry not in name_set:
            fail(f"core required file missing: {relative_path}")
        try:
            read_entry(entry).decode("utf-8")
        except UnicodeDecodeError:
            fail(f"core required file is not UTF-8: {relative_path}")

    for relative_path in optional_load_sequence:
        entry = f"SYSTEM_CORE/{relative_path}"
        if entry not in name_set:
            continue
        try:
            read_entry(entry).decode("utf-8")
        except UnicodeDecodeError:
            # Optional non-UTF-8 files are degraded-load compatible.
            continue


def validate_core_zip(zip_path: Path) -> None:
    names = validate_no_backslash_entries(zip_path)
    top = {name.split("/", 1)[0] for name in names if name}

    if top != {"SYSTEM_CORE", "SKILLS"}:
        fail(f"invalid core ZIP root in {zip_path.relative_to(REPO_ROOT)}: {sorted(top)}")
    if any(name.startswith("GPT.SKILLS/") for name in names):
        fail("core ZIP contains GPT.SKILLS wrapper")
    if any(name.lower().endswith(".zip") for name in names):
        fail("core ZIP contains nested zip")

    required = {
        "SYSTEM_CORE/MANIFEST.json",
        "SYSTEM_CORE/ENTRY.md",
        "SYSTEM_CORE/README.md",
        "SYSTEM_CORE/SEMANTICS.md",
        "SYSTEM_CORE/OPERATIONAL_RULES.md",
        "SKILLS/README.md",
    }
    missing = sorted(required - set(names))
    if missing:
        fail("core ZIP missing required entries:\n" + "\n".join(missing))

    with zipfile.ZipFile(zip_path) as archive:
        manifest = json.loads(archive.read("SYSTEM_CORE/MANIFEST.json").decode("utf-8"))

        validate_core_manifest(manifest, names, archive.read)

    if manifest.get("load_sequence") != [
        "ENTRY.md",
        "README.md",
        "SEMANTICS.md",
        "OPERATIONAL_RULES.md",
    ]:
        fail("core manifest load_sequence changed")


def resolve_declared_path(source: Path, relative_path: str) -> Path:
    return source.joinpath(*PurePosixPath(relative_path).parts)


def require_declared_file(source: Path, relative_path: str, field: str) -> Path:
    path = resolve_declared_path(source, relative_path)
    if not path.exists():
        fail(f"{field} declares missing file: {relative_path}")
    if path.is_dir():
        fail(f"{field} declares directory target: {relative_path}")
    return path


def require_utf8_file(path: Path, relative_path: str, field: str) -> None:
    try:
        path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail(f"{field} declares non-UTF-8 file: {relative_path}")


def validate_skill_manifest(source: Path, manifest: dict) -> str:
    skill_name = manifest.get("skill_name")
    if not isinstance(skill_name, str) or not skill_name:
        fail(f"invalid skill_name in {(source / 'MANIFEST.json').relative_to(REPO_ROOT)}")
    if source.name != skill_name:
        fail(f"skill source folder must match skill_name: {source.name} != {skill_name}")
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        fail(f"invalid version in {(source / 'MANIFEST.json').relative_to(REPO_ROOT)}")

    primary_present = "primary_file" in manifest
    load_present = "load_sequence" in manifest
    if primary_present != load_present:
        fail("primary_file and load_sequence must either both be present or both be omitted")

    if primary_present:
        primary_file = manifest["primary_file"]
        if not isinstance(primary_file, str) or not is_safe_relative_path(primary_file):
            fail(f"primary_file must be a safe relative path: {primary_file!r}")
        load_sequence = require_string_array(manifest, "load_sequence", required=True)
        if not load_sequence:
            fail("load_sequence must not be empty")
        if primary_file not in load_sequence:
            fail("primary_file must be included in load_sequence")
    else:
        primary_file = "SKILL.md"
        load_sequence = ["SKILL.md"]

    support_files = require_string_array(manifest, "support_files")
    tool_files = require_string_array(manifest, "tool_files")
    asset_files = require_string_array(manifest, "asset_files")

    overlap = set(load_sequence).intersection(support_files)
    if overlap:
        fail("load_sequence and support_files overlap: " + ", ".join(sorted(overlap)))

    for relative_path in load_sequence:
        path = require_declared_file(source, relative_path, "load_sequence")
        require_utf8_file(path, relative_path, "load_sequence")
        if path.suffix.lower() in SCRIPT_EXTENSIONS:
            fail(f"load_sequence must not include script/executable file: {relative_path}")

    for relative_path in support_files:
        require_declared_file(source, relative_path, "support_files")

    for relative_path in tool_files:
        path = require_declared_file(source, relative_path, "tool_files")
        require_utf8_file(path, relative_path, "tool_files")

    for relative_path in asset_files:
        require_declared_file(source, relative_path, "asset_files")

    return skill_name


def validate_skill_zip(zip_path: Path, skill_name: str) -> None:
    names = validate_no_backslash_entries(zip_path)
    top = {name.split("/", 1)[0] for name in names if name}

    if len(top) == 1 and "MANIFEST.json" not in top:
        fail(f"skill ZIP contains single wrapper directory: {sorted(top)[0]}/")
    if any(name.startswith("GPT.SKILLS/") for name in names):
        fail("skill ZIP contains GPT.SKILLS wrapper")
    if any(name.lower().endswith(".zip") for name in names):
        fail("skill ZIP contains nested zip")
    if "MANIFEST.json" not in names:
        fail("skill ZIP must contain MANIFEST.json at root")

    with zipfile.ZipFile(zip_path) as archive:
        manifest = json.loads(archive.read("MANIFEST.json").decode("utf-8"))

    if manifest.get("skill_name") != skill_name:
        fail(f"skill_name mismatch for {zip_path.name}")


def build_core() -> Path:
    output = DIST / "GPT.SKILLS.zip"
    write_zip(CORE_SOURCE, output)
    validate_core_zip(output)
    return output


def build_skills() -> list[Path]:
    if not SKILL_SOURCES.exists():
        return []

    SKILL_DIST.mkdir(parents=True, exist_ok=True)
    built: list[Path] = []

    for source in sorted(path for path in SKILL_SOURCES.iterdir() if path.is_dir()):
        manifest_path = source / "MANIFEST.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        skill_name = validate_skill_manifest(source, manifest)

        output = SKILL_DIST / f"{skill_name}.zip"
        write_zip(source, output)
        validate_skill_zip(output, skill_name)
        built.append(output)

    return built


def main() -> int:
    built = [build_core(), *build_skills()]
    for path in built:
        print(f"built {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
