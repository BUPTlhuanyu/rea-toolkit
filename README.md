# rea-toolkit

[中文](README.ZH.md) | English

A repository for managing reconstruction / reverse-engineering skills.

## Documentation

- [docs/README.md](docs/README.md): documentation index
- [docs/FILES.md](docs/FILES.md): file-by-file repository map
- [docs/WORKSPACE-TEMPLATE.md](docs/WORKSPACE-TEMPLATE.md): detailed workspace-template workflow

## Repository layout

```
rea-toolkit/
├── skills/
│   ├── reconstruction-bootstrap/   # natural-language entry + profiles/
│   ├── reconstruction-core/        # generic pipeline, evidence contract, workspace template
│   └── reconstruction-scaffold/    # generate workspace + domain config
├── profiles -> skills/reconstruction-bootstrap/profiles   # compatibility symlink
├── toolkits/                       # generic tools: capture, crop, compare, regression, Frida, rea
├── bin/rea-toolkit.js              # npx installer
├── package.json
├── README.md                       # English
└── README.ZH.md                    # Chinese
```

The **canonical location** of `profiles/` is
`skills/reconstruction-bootstrap/profiles/`. This way `npx skills add` copies the
profiles together with the bootstrap skill. The top-level `profiles` entry is only a
compatibility symlink.

Every skill follows:

```
skills/<skill-name>/
├── SKILL.md
├── scripts/
├── references/
└── templates/
```

## Installation

Comate discovers skills through `SKILL.md`. Installation therefore means putting the
three directories `reconstruction-bootstrap` / `reconstruction-core` /
`reconstruction-scaffold` where Comate can find them. They must be installed together.

### Option 1: `npx skills` (generic CLI)

`npx skills` is the generic installer from the skills.sh ecosystem. It supports local
paths, GitHub repositories, and skill packages. It installs to `.agents/skills/`
(project-level) or `~/.agents/skills/` (global); Comate scans both `.comate/skills/`
and `.agents/skills/`.

```bash
# Global: ~/.agents/skills/
npx --yes skills add /path/to/rea-toolkit -g -y -a universal

# Project-level: <project>/.agents/skills/
npx --yes skills add /path/to/rea-toolkit -y -a universal

# After publishing to GitHub
npx --yes skills add <owner/repo> -g -y -a universal
```

Notes:

- `-g` means global; omit it for project-level installation.
- `-a universal` is the generic agent target; `npx skills` does not currently support
  `-a comate`.
- It only installs the `SKILL.md` directories. Because `profiles/` lives under
  `skills/reconstruction-bootstrap/profiles/`, the three skills bring the profiles
  with them.
- `toolkits/` is not installed by `npx skills`. Use the full installer below, or
  clone this repository, if you need the generic tools.

### Option 2: `npx rea-toolkit` (full installation)

The repository ships `bin/rea-toolkit.js`, which installs **skills + profiles +
toolkits**:

```bash
# Project-level: <project>/.comate
npx --yes /path/to/rea-toolkit install --project <project>

# Global: ~/.comate
npx --yes /path/to/rea-toolkit install --global

# Development: symlink instead of copying
npx --yes /path/to/rea-toolkit install --project <project> --link

# Check
npx --yes /path/to/rea-toolkit doctor --project <project>
npx --yes /path/to/rea-toolkit doctor --global
```

If the package is published to an npm registry, the path can be omitted:

```bash
npx rea-toolkit install --global
```

`package.json` currently has `private: true`; remove it before publishing to a registry.

Note: `npx` only downloads and runs a package. It does **not** register a skill
globally by itself. "Global" is decided by the installer's `--global` flag, which
copies files to `~/.comate/skills/`. The installer copies by default so that cleaning
the npx cache does not leave broken symlinks. Use `--link` during development.

### Option 3: manual copy / symlink

Project-level:

```bash
mkdir -p <project>/.comate/skills
ln -s /path/to/rea-toolkit/skills/reconstruction-bootstrap \
  <project>/.comate/skills/reconstruction-bootstrap
ln -s /path/to/rea-toolkit/skills/reconstruction-core \
  <project>/.comate/skills/reconstruction-core
ln -s /path/to/rea-toolkit/skills/reconstruction-scaffold \
  <project>/.comate/skills/reconstruction-scaffold
```

Global:

```bash
mkdir -p ~/.comate/skills
ln -s /path/to/rea-toolkit/skills/reconstruction-bootstrap \
  ~/.comate/skills/reconstruction-bootstrap
ln -s /path/to/rea-toolkit/skills/reconstruction-core \
  ~/.comate/skills/reconstruction-core
ln -s /path/to/rea-toolkit/skills/reconstruction-scaffold \
  ~/.comate/skills/reconstruction-scaffold
```

`profiles/` already lives inside `reconstruction-bootstrap/profiles/`, so you do not
need a separate profiles symlink when linking the skill manually. If another tool
needs the top-level `profiles/`, add:

```bash
ln -s /path/to/rea-toolkit/profiles <project>/.comate/profiles
```

Profiles can also be placed in any of these locations (searched in order):

1. `$RECONSTRUCTION_PROFILES`
2. `<bootstrap-skill>/profiles/` (included automatically by `npx skills`)
3. `<rea-toolkit>/profiles/`
4. `<project>/.comate/profiles/`
5. `<project>/profiles/`
6. `<cwd>/profiles/`

After installation / reload, the current session's skill list should contain:

- `reconstruction-bootstrap`
- `reconstruction-core`
- `reconstruction-scaffold`

Existing WPS projects keep using their own
`.comate/skills/wps-chart-source-reconstruction/` and workspace; no change is needed.

### Option 4: run directly (no skill installation)

If you only want to run the scripts, installation is optional:

```bash
python3 /path/to/rea-toolkit/skills/reconstruction-bootstrap/scripts/bootstrap.py \
  --profile wps-chart --check-only
```

This does not let the model trigger the skill automatically; it is for manual use only.

## Recommended usage: state the goal

No manual commands are required. Tell the model:

- "Build me a project for decompiling the WPS desktop application."
- "Initialize an Android app reverse-engineering project."
- "Set up a Unity game reconstruction workspace."
- "Reconstruct this web app from scratch; create the project first."

`reconstruction-bootstrap` will:

1. choose a platform profile from the description;
2. ask only for missing blocking information;
3. generate `.comate/reconstruction-<domain>/`;
4. check toolchains such as rea / adb / frida;
5. initialize the capability ledger;
6. hand over to `reconstruction-core`.

## Generic tools

Tools extracted from the WPS chart reconstruction project, with domain constants
removed, live in `toolkits/`:

- `toolkits/image/`: crop, diff, contact sheet, connected components / text-line measurement
- `toolkits/metrics/`: global MAE + `maxBlock` / `focusBlocks` + ΔE local clusters + edge structure
- `toolkits/compare/`: reference/target stacking + focus metrics
- `toolkits/capture/`: macOS window-ID capture
- `toolkits/ooxml/`: xlsx chart XML / cell patching
- `toolkits/regress/`: generic regression runner
- `toolkits/frida/`: spawn/attach + JSONL
- `toolkits/rea/`: rea MCP batch processing

See `toolkits/README.md` for usage and dependencies. WPS-specific wrappers remain in
the WPS workspace.

## Platform matrix

| Platform | Profile | Source evidence | Effect evidence |
|---|---|---|---|
| Native desktop | `desktop-native` | disassembly / decompilation / debugger | UI screenshot / tree |
| Android | `android-native` | rea/jadx, smali, Frida | adb screenshot + UI tree + logcat |
| iOS | `ios-native` | Mach-O, class-dump, LLDB | device screenshot + syslog |
| 3D games | `unity-game` / `unreal-game` | IL2CPP / pak / assets | frame sequence + scene state |
| 2D games | `game-2d` | script bundles / assets / engine metadata | frame sequence + game state |
| Web | `web-app` | build artifacts / source maps / network | screenshot + DOM / network |
| WPS charts | `wps-chart` | kso.framework decompilation | WPS screenshot + regression |

## Manual usage

### Existing project, workspace only

```bash
python3 skills/reconstruction-core/scripts/ensure_workspace.py
```

### New domain, generate a scaffold first

```bash
python3 skills/reconstruction-scaffold/scripts/scaffold.py \
  --domain unity-3d \
  --root /path/to/project \
  --profile unity-game \
  --source-root src \
  --reference-runtime "./run-ref.sh" \
  --target-runtime "npm run build" \
  --comparison screenshot
```

`--profile` can be a name under `profiles/` or a file path; `.json` is preferred.
A JSON profile also generates `profile.json` and `domain.md`, and enables toolchain
checks.

### Check toolchains only

```bash
python3 skills/reconstruction-bootstrap/scripts/bootstrap.py \
  --profile wps-chart --check-only
```

### rea configuration

`rea` depends on `JAVA_HOME`, `REA_JADX_MCP_JAR`, and `mcpServers.rea` in
`~/.comate/mcp.json`. If any is missing:

```bash
python3 skills/reconstruction-bootstrap/scripts/bootstrap.py \
  --profile wps-chart --check-only --fix-mcp
```

`--fix-mcp` only fills missing fields, backs up the existing config first, and never
overwrites existing values. Unresolved `${VAR}` values produce
`MCP_CONFIG_NEEDS_MANUAL`.

## Adding a skill

1. Create a directory under `skills/` named after the skill (lowercase letters,
   digits, and hyphens).
2. Write `SKILL.md` with this frontmatter:

```markdown
---
name: <skill-name>
description: Explain what this skill does and when to use it
---
```

`description` determines when the skill is triggered, so state the usage scenarios
clearly.
