# Packaging GPT.SKILLS.zip

Use `scripts/build_packages.py` to create runtime packages.

To create the runtime package, zip the contents of `GPT.SKILLS/`, not the wrapper folder.

Correct ZIP root:

```text
SYSTEM_CORE/
SKILLS/
```

Wrong ZIP root:

```text
GPT.SKILLS/
  SYSTEM_CORE/
  SKILLS/
```

Reason:

`SKILL CORE UNPACK` extracts `GPT.SKILLS.zip` into:

```text
/mnt/data/GPT.SKILLS/
```

If the ZIP contains the wrapper folder, the extracted tree becomes:

```text
/mnt/data/GPT.SKILLS/GPT.SKILLS/SYSTEM_CORE/
```

That tree is invalid for the current runtime.

## Check

Before using `GPT.SKILLS.zip`, open it and confirm the first level contains:

```text
SYSTEM_CORE/
SKILLS/
```

The first level must not contain:

```text
GPT.SKILLS/
```

ZIP entries must use POSIX `/` separators.

Valid:

```text
SYSTEM_CORE/MANIFEST.json
SKILLS/README.md
```

Invalid:

```text
SYSTEM_CORE\MANIFEST.json
SKILLS\README.md
```

No ZIP entry may contain `\`.

The build script must fail if any generated or checked ZIP contains `\` in an entry name.
