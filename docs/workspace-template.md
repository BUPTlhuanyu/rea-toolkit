# Reconstruction Workspace Template: Workflow and File Reference

[中文](WORKSPACE-TEMPLATE.ZH.md) | English

This document covers exactly one object:

```text
skills/reconstruction-core/templates/workspace/
```

It is the workspace template copied into a project by
`reconstruction-scaffold` / `reconstruction-bootstrap`. This document follows the
current template contents strictly. `domain.md`, `profile.json`, `bootstrap.json`,
`capabilities/<feature-id>/README.md`, and similar files are generated during
initialization or use; they are not part of the template.

Companion diagrams:

- [Architecture: components and data flow](diagrams/workspace-template-architecture.html)
- [Workflow: 6 stages](diagrams/workspace-template-workflow.html)

> The workflow diagram merges Stage 5-6 into one closing node; this document still
> describes Stage 5 and Stage 6 separately.

---

## 1. What problem does the template solve?

The easiest way for reconstruction work to get out of control is not writing code.
It is:

1. not knowing how far a feature has actually been reconstructed;
2. not knowing which function, case, or run a conclusion came from;
3. not being able to find earlier evidence after switching models or returning a
   week later;
4. artifacts scattered across `tmp/`, `runs/foo-001/`, `cases2/`, making regression
   impossible.

The template solves these four problems with fixed directories, fixed state, and a
fixed evidence contract:

```text
input -> evidence -> case -> implementation -> run -> conclusion
```

Every step must land in a fixed path and remain findable by the next person.

---

## 2. Template directory, file by file

The complete current template:

```text
templates/workspace/
├── PIPELINE.md
├── README.md
├── state.json
├── capabilities/
│   ├── README.md
│   ├── _TEMPLATE/
│   │   └── README.md
│   ├── index.json
│   └── case-manifest.json
├── corpus/
│   ├── provided/
│   │   └── README.md
│   └── derived/
│       └── README.md
├── evidence/
│   ├── source/
│   │   └── README.md
│   ├── runtime/
│   │   └── README.md
│   └── audit/
│       └── README.md
├── runs/
│   ├── _TEMPLATE/
│   │   ├── README.md
│   │   └── run.json
│   ├── regress-baseline/
│   │   └── README.md
│   └── regress-current/
│       └── README.md
├── tools/
│   ├── INDEX.md
│   └── capabilities/
│       ├── build_capability_index.py
│       ├── build_feature_dossiers.py
│       ├── show_capability.py
│       └── validate_capability_ids.py
└── history/
    ├── legacy-probes/
    │   └── README.md
    ├── plans/
    │   └── README.md
    ├── rounds/
    │   └── README.md
    ├── source-backups/
    │   └── README.md
    └── state-backups/
        └── README.md
```

### 2.1 Root files

| File | Purpose | Written by | Safe to edit by hand? |
|---|---|---|---|
| `PIPELINE.md` | Single entry point for the process: 6 stages, directory contract, gates, hard rules | scaffold copies the template | Only when changing the process |
| `README.md` | Workspace map: directories, `case.json`, shortest onboarding path | scaffold copies the template | Can be extended |
| `state.json` | Machine state: features / backlog / queue / runScope | Humans + tools | **Yes; it is the state source of truth** |

#### `PIPELINE.md`

It is the contract for *how to work*, not a project log. It contains:

- the directory contract: where inputs, evidence, and run artifacts live;
- naming: feature-id, case-id, run-id, evidence file names;
- the two status axes: source / effect;
- the 6 stages and their gates;
- the capability dossier template: `capabilities/_TEMPLATE/README.md`;
- hard rules that prevent "a new model invents a new process";
- common commands and context-efficiency rules.

> A dossier is the file/story of one capability, not a code template. Every
> capability eventually has `capabilities/<feature-id>/README.md`.

Read it **first** when entering the workspace; do not rely on memory.

#### `README.md`

The workspace map, answering "where do things go":

- the directory tree;
- the `case.json` shape;
- ledger generation / validation commands;
- shortest paths.

It does not replace `PIPELINE.md`: `PIPELINE.md` is the process, `README.md` is the
map.

#### `state.json`

The template starts with an empty state:

```javascript
{
  // State-file schema version
  "schemaVersion": 1,
  // Current workspace phase/mode; the template starts at BOOTSTRAP
  "currentState": "BOOTSTRAP",
  // Number of work rounds/iterations executed
  "iteration": 0,
  // Capability inventory status; the template starts at INCOMPLETE
  "inventoryStatus": "INCOMPLETE",
  // Scope selected for the current task batch/run; this is NOT the full ledger
  // The full ledger is features (or capabilities/index.json)
  "runScope": {
    // Capability IDs to process in this batch
    "features": [],
    // Case IDs that must be run/confirmed in this batch
    "requiredCases": [],
    // Regressions/commands that must pass in this batch
    "requiredRegressions": []
  },
  // The single capability currently selected; null = none
  "selectedFeature": null,
  // Execution status: IDLE / RUNNING / BLOCKED / DONE
  "executionStatus": "IDLE",
  // Resume note: what to do first when resuming
  "resumeAction": "",
  // Unfinished task/agent task IDs
  "pendingTaskIds": [],
  // Whether the current state is safe to resume directly
  "safeToResume": true,
  // Pending capability queue; the head has priority
  "queue": [],
  // Queue source / generation basis
  "queueSource": "",
  // Blocked items: capability ID + reason + unblock condition
  "blocked": [],
  // What the previous round actually did
  "lastAction": "",
  // Previous verification verdict: tests/build/regression
  "lastVerdict": "",
  // Full capability ledger: all capabilities; this is NOT runScope
  "features": [],
  // Environment snapshot: reference/target/binary/version/etc.
  "environment": {},
  // Candidate capabilities / gaps
  "backlog": []
}
```

`features` is the source of capability state. Each entry looks roughly like:

```javascript
{
  // Semantic capability ID: <domain>.<feature>[.<variant>]
  "key": "<domain>.<feature>",
  // Human-readable name
  "featureName": "...",
  // Category / group
  "category": "...",
  // Source axis: UNKNOWN / LOCATED / DECODED / EXACT / PARTIAL / NONPORTABLE
  "sourceStatus": "UNKNOWN",
  // Effect axis: PENDING / MATCH / DIFF / NO_REFERENCE / ACCEPTED_NONPORTABLE
  "effectStatus": "PENDING",
  // Source evidence refs: evidence/source/... or function addresses
  "sourceRefs": [],
  // Effect evidence refs: screenshots / cmp / run
  "effectImageRefs": [],
  // Related case IDs
  "caseRefs": [],
  // Source verdict summary
  "sourceVerdict": "",
  // Source gaps / unresolved points
  "sourceGap": "",
  // Effect verdict summary
  "effectVerdict": "",
  // Regression status: PASS / FAIL / REGRESSION / NOT_RUN
  "regressionStatus": "",
  // Next action
  "nextState": "",
  // Summary of the last change
  "lastChange": ""
}
```

Rules:

- `key` must be a semantic ID, e.g. `pie3d.flat-import-inset`;
- do not use batch numbers such as `ext-47` or `case-42` as capability IDs;
- `sourceStatus` and `effectStatus` are independent axes;
- `index.json` is generated from this file. **Do not edit index and expect state to
  update in reverse.**

`runScope` is the work order for "the capabilities/cases/regressions selected for
this task", not the full ledger:

- `features`: the full capability ledger (all capabilities)
- `runScope`: the subset selected for the current task batch
- `queue`: the prioritized pending queue
- `selectedFeature`: the single capability currently being worked on

> The code blocks below are documentation only and use `javascript` highlighting;
> actual JSON files cannot contain comments.

### 2.2 `capabilities/`

This is the most easily misunderstood directory in the template. It contains:

- the capability index (`index.json`);
- the case mapping (`case-manifest.json`);
- the capability catalog (`README.md`);
- the new-capability template (`_TEMPLATE/README.md`).

#### `capabilities/index.json`

The template contains an empty ledger:

```javascript
{
  // Ledger schema version
  "schemaVersion": 1,
  // Generation date (YYYY-MM-DD)
  "generatedAt": "",
  // Generation sources
  "sources": [],
  // Summary statistics
  "summary": {
    // Total capabilities
    "capabilities": 0,
    // Case statistics
    "cases": {
      // Total cases
      "total": 0,
      // Provided cases
      "provided": 0,
      // Derived cases
      "derived": 0,
      // Cases mapped to capabilities
      "mapped": 0,
      // Unmapped cases
      "unmapped": 0
    }
  },
  // Capability table: status, evidence refs, case refs per capability
  "capabilities": [],
  // Candidate capabilities / gaps
  "backlog": []
}
```

After use, `build_capability_index.py` overwrites it with:

- each capability's `id/name/category/kind/tags`;
- `completion`;
- `source.status`, `source.refs`, `source.verdict`, `source.gap`;
- `effect.status`, `effect.refs`, `effect.verdict`;
- `cases.refs`, `cases.verdicts`;
- `regressionStatus`, `nextState`, `lastChange`, `details`.

**Do not edit by hand.** Change `state.json` / `case.json` and regenerate.

#### `capabilities/case-manifest.json`

The template contains an empty manifest:

```javascript
{
  // Manifest schema version
  "schemaVersion": 1,
  // Generation date (YYYY-MM-DD)
  "generatedAt": "",
  // Mapping note: capabilities is a candidate set; refine it per case when editing
  "mappingNote": "capabilities is a candidate set; refine per case when editing it.",
  // Case summary
  "summary": {
    // Total cases
    "total": 0,
    // Provided cases
    "provided": 0,
    // Derived cases
    "derived": 0,
    // Cases mapped to capabilities
    "mapped": 0,
    // Unmapped cases
    "unmapped": 0
  },
  // Case list: which capabilities each case covers
  "cases": []
}
```

After use, `build_capability_index.py` merges:

1. `corpus/**/case.json`;
2. cases with an `id` in `evidence/audit/*.json`;
3. the previous `case-manifest.json` (manual entries win by `id`).

Each case entry contains:

```javascript
{
  // Case ID: <group>/<case>
  "id": "<group>/<case>",
  // Origin: provided = user/upstream, derived = derived from source
  "origin": "provided|derived",
  // Kind: fixture / screenshot / trace / etc.
  "kind": "fixture",
  // Case name
  "name": "...",
  // Path relative to the workspace
  "path": "corpus/...",
  // Capability IDs covered by this case
  "capabilities": ["<domain>.<feature>"],
  // Mapping source: declared / audit / manual / unmapped
  "mapping": "declared|audit|manual|unmapped",
  // Effect verdict
  "effect": { "status": "PENDING", "notes": "" },
  // Source verdict
  "source": { "status": "PENDING", "notes": "" }
}
```

Prefer writing `corpus/**/case.json` for new cases; do not edit
`case-manifest.json` directly.

#### `capabilities/README.md`

The template contains an empty catalog. After use, `build_capability_index.py`
overwrites it, grouped by `category`:

```text
### <category>
- [`<feature-id>`](<feature-id>/README.md) — <name> (source ..., effect ...)
```

**Do not edit by hand.**

#### `capabilities/_TEMPLATE/README.md`

The template for a new capability dossier. Copy it to:

```text
capabilities/<feature-id>/README.md
```

It contains:

- observed behavior;
- source/protocol evidence (address/function/formula/boundary);
- case table;
- implementation files;
- verification / run;
- gaps / next step.

#### `capabilities/<feature-id>/README.md` (generated during use)

The dossier of a single capability, and the single narrative entry point for "how
this feature was reconstructed".

- Generated block:

  ```markdown
  <!-- GENERATED:START -->
  ...
  <!-- GENERATED:END -->
  ```

  Maintained by `build_feature_dossiers.py`; do not edit by hand.

- Outside the block: manual notes; the generator does not overwrite them.

### 2.3 `corpus/`

The template contains only two READMEs and no actual cases.

| Path | Purpose | What the template contains |
|---|---|---|
| `corpus/provided/` | Real inputs provided by users/upstream; covers real scenarios; no minimality requirement | `README.md` |
| `corpus/derived/` | **Minimal attributable cases** derived from source/protocol evidence | `README.md` |

After use, each case directory contains `case.json`:

```javascript
{
  // Case ID: <group>/<case>
  "id": "<group>/<case>",
  // Origin: provided = user/upstream, derived = derived from source
  "origin": "provided|derived",
  // Kind: fixture / screenshot / trace / etc.
  "kind": "fixture",
  // Capability IDs covered by this case
  "capabilities": ["<domain>.<feature>"],
  // Effect verdict
  "effect": { "status": "PENDING" },
  // Source verdict
  "source": { "status": "PENDING" }
}
```

"Minimal" means the fewest variables, stable triggering of one branch, and an
observable result; it does not mean the smallest file or input. Interactions are
tested pairwise only.

### 2.4 `evidence/`

The template contains only three READMEs and no actual evidence.

| Path | Purpose | Typical files after use |
|---|---|---|
| `evidence/source/` | Static decompilation / protocol conclusions | `<feature-id>-<date>.md` |
| `evidence/source/raw/<date>/` | Raw dumps/crops, frozen | `MANIFEST.md` + raw files |
| `evidence/runtime/` | Runtime probes / hooks / traces / logs | `<feature-id>-<date>.jsonl` |
| `evidence/runtime/raw/<date>/` | Session-level raw logs, frozen | `MANIFEST.md` + raw logs |
| `evidence/audit/` | Per-case source/effect verdicts (optional) | `*.json` |

Rules:

- feature-id is the primary key; dates are only for provenance;
- raw dumps go in `raw/`; conclusions do not;
- every file under `raw/` must be mapped in `MANIFEST.md`;
- negative results are evidence too.

### 2.5 `runs/`

| Path | Purpose | What the template contains |
|---|---|---|
| `runs/_TEMPLATE/` | Template for a new run | `README.md` + `run.json` |
| `runs/regress-baseline/` | Current regression baseline, read-only | `README.md` |
| `runs/regress-current/` | Latest regression's disposable output, safe to overwrite | `README.md` |
| `runs/<run-id>/` | Formal record of one experiment/regression | Created during use |
| `runs/archive/` | Frozen history | Created during use |

`_TEMPLATE/run.json`:

```javascript
{
  // Run ID: YYYY-MM-DD-<feature-id>-NN
  "runId": "YYYY-MM-DD-<feature-id>-NN",
  // Capability ID for this run
  "feature": "<feature-id>",
  // Run date
  "date": "YYYY-MM-DD",
  // Reproduction command
  "command": "<reproduction command>",
  // Baseline path
  "baseline": "runs/regress-baseline",
  // Cases included in this run
  "cases": [],
  // Overall result: PENDING / MATCH / DIFF / REGRESSION
  "result": "PENDING",
  // Regressions
  "regressions": [],
  // Notes
  "notes": ""
}
```

Formal run directory:

```text
runs/<run-id>/
├── run.json
├── result.json
├── shots/          # or frames/, traces/
└── logs/
```

`regress-baseline` is updated only by the baseline refresh flow;
`regress-current` is not long-term evidence.

### 2.6 `tools/`

| File | Purpose | Input | Output |
|---|---|---|---|
| `INDEX.md` | Tool index | none | documentation |
| `capabilities/build_capability_index.py` | Generate the capability ledger | `state.json`, `corpus/**/case.json`, `evidence/audit/*.json`, previous manifest | `index.json`, `case-manifest.json`, `README.md` |
| `capabilities/build_feature_dossiers.py` | Generate/refresh dossiers | `index.json`, `case-manifest.json` | `capabilities/<feature-id>/README.md` |
| `capabilities/show_capability.py` | Compact view of one capability | `index.json`, `case-manifest.json` | terminal summary |
| `capabilities/validate_capability_ids.py` | Validate IDs/status/cases/dossiers | the above + `state.json` + `profile.json` | `OK` / error list |

Standard order:

```bash
python3 tools/capabilities/build_capability_index.py
python3 tools/capabilities/build_feature_dossiers.py
python3 tools/capabilities/validate_capability_ids.py
```

### 2.7 `history/`

Frozen archive; not an input to new work:

| Path | Contents |
|---|---|
| `history/legacy-probes/` | Old probes, possibly depending on deleted builds |
| `history/plans/` | Old plans, verification notes, one-off checklists |
| `history/rounds/` | Parallel-round rules, patches, request results |
| `history/source-backups/` | `.orig` / rejected source backups |
| `history/state-backups/` | 1–2 state snapshots from before major migrations |

---

## 3. How the template is instantiated

The template is not a workspace; it is copied into one. Initialization has two
layers.

### 3.1 `reconstruction-scaffold`

`skills/reconstruction-scaffold/scripts/scaffold.py`:

1. validates `--domain`;
2. copies `reconstruction-core/templates/workspace` to
   `<project>/.comate/reconstruction-<domain>/`;
3. replaces `<workspace>` in `PIPELINE.md` / `README.md` with the real path;
4. resolves the profile:
   - JSON profile → generate `domain.md` + `profile.json`;
   - Markdown profile → copy as `domain.md`;
   - no profile → generate from `templates/domain.md`;
5. writes the project config `<project>/.comate/reconstruction-<domain>.json`.

### 3.2 `reconstruction-bootstrap`

`skills/reconstruction-bootstrap/scripts/bootstrap.py`:

1. resolves the profile;
2. calls `scaffold.py` to create the workspace;
3. calls `check_tools.py` to check rea/adb/frida and other tools;
4. calls `ensure_workspace.py` to confirm the workspace;
5. runs:
   - `build_capability_index.py`
   - `build_feature_dossiers.py`
   - `validate_capability_ids.py`
6. writes `bootstrap.json` (profile, tool checks, ledger counts).

### 3.3 `ensure_workspace.py`

`skills/reconstruction-core/scripts/ensure_workspace.py`:

- resolution order: `--workspace` → `RECONSTRUCTION_WORKSPACE` → project config →
  existing `.comate/*/state.json` → `.comate/reconstruction`;
- copies the template when the workspace does not exist;
- never overwrites an existing workspace;
- prints `WORKSPACE_READY` / `WORKSPACE_CREATED` / `CONFIG`.

---

## 4. The 6-stage workflow

### Stage 0 — Intake

**Input**: user cases, source clues, backlog.

**Actions**:

1. assign a feature-id;
2. copy `capabilities/_TEMPLATE/README.md` to
   `capabilities/<feature-id>/README.md`;
3. add the capability to `state.json#features`;
4. declare the capability in `corpus/.../case.json`;
5. run build + validate.

**Outputs**:

```text
capabilities/<feature-id>/README.md
state.json#features
corpus/.../case.json
```

**Gate**: `validate_capability_ids.py` passes, and you can answer "which observable
behavior is being reconstructed".

### Stage 1 — Source

**Input**: decompilation, debugger, protocol capture, runtime hooks.

**Actions**:

1. locate functions/branches/constants/defaults/boundaries;
2. record addresses, pseudo-code, call chains;
3. distinguish EXACT / PARTIAL / FITTED.

**Outputs**:

```text
evidence/source/<feature-id>-<date>.md
evidence/source/raw/<date>/ (if applicable)
```

**Gate**: `sourceStatus >= DECODED`, and at least one case can be constructed.

### Stage 2 — Case

**Input**: the branch table from Stage 1.

**Actions**:

1. at least one case per branch: default / explicit override / boundary;
2. interactions are tested pairwise only;
3. put cases in `corpus/derived/<group>/<case>/`;
4. declare `capabilities` in `case.json`.

**Outputs**:

```text
corpus/derived/<group>/<case>/
corpus/derived/<group>/<case>/case.json
```

**Gate**: the case can be opened/executed by the reference implementation, and the
input is reproducible.

### Stage 3 — Reference

**Input**: cases from Stage 2.

**Actions**:

1. run the case with the reference command from `domain.md`;
2. save raw output and normalized artifacts;
3. record reference version, capture method, and validity.

**Outputs**:

```text
corpus/.../reference/
evidence/runtime/<feature-id>-<date>.jsonl
```

**Gate**: reference output status is `ok`; invalid captures must be marked
`INVALID`.

### Stage 4 — Implement

**Input**: source conclusions from Stage 1 + references from Stage 3.

**Actions**:

1. change only the target implementation and its tests;
2. record files/functions/formulas/source mappings in the dossier.

**Gate**: typecheck, unit tests, and build pass.

### Stage 5 — Verify

**Input**: Stage 4 code.

**Actions**:

1. single case: rerun the target, generate comparison artifacts, record the verdict;
2. targeted regression: select cases by input features/code paths;
3. run a full regression when necessary;
4. write results to `runs/<run-id>/`.

**Outputs**:

```text
runs/<run-id>/
├── run.json
├── result.json
├── shots/
└── logs/
```

**Gate**:

- `effect = MATCH` or `ACCEPTED_NONPORTABLE`;
- no new regressions;
- cases with diffs have their reason and status recorded in the dossier.

### Stage 6 — Close

**Actions**:

1. update source/effect/nextState in `state.json#features`;
2. rebuild `capabilities/index.json`;
3. refresh dossiers;
4. update the dossier's verdict/evidence/next step;
5. write old problems exposed by regression into `evidence/source/` and add a
   backlog entry.

**Gate**:

```bash
python3 tools/capabilities/build_capability_index.py
python3 tools/capabilities/build_feature_dossiers.py
python3 tools/capabilities/validate_capability_ids.py
```

They must pass, and the dossier must independently answer:

- What behavior was observed?
- What is the source/protocol evidence?
- Which cases were used?
- Where is the reference output?
- What changed in the target implementation?
- What is the final verdict? What remains?

---

## 5. Data flow: who generates what

```text
state.json#features ─────────────┐
corpus/**/case.json ─────────────┼─> build_capability_index.py
evidence/audit/*.json ───────────┘        │
                                          ├─> capabilities/index.json
                                          ├─> capabilities/case-manifest.json
                                          └─> capabilities/README.md
                                                    │
                                                    v
                                     build_feature_dossiers.py
                                                    │
                                                    v
                          capabilities/<feature-id>/README.md
                                                    │
                                                    v
                                     validate_capability_ids.py
```

Key points:

- `state.json` is the source of capability state;
- `case.json` is the explicit case → capability mapping;
- `index.json` / `case-manifest.json` / `README.md` are derived files;
- the dossier is the narrative entry point for conclusions;
- `validate` is the final gate.

---

## 6. Files that should not be edited by hand

| File | Reason |
|---|---|
| `capabilities/index.json` | Overwritten by `build_capability_index.py` |
| `capabilities/case-manifest.json` | Re-merged; add new cases via `case.json` |
| `capabilities/README.md` | Overwritten by the generator |
| The dossier's `GENERATED` block | Maintained by `build_feature_dossiers.py` |
| `runs/regress-baseline/` | Updated only by the baseline refresh flow |
| `history/` | Frozen archive |

## 7. Files that are safe to edit

- `state.json#features` / `backlog` / `queue`
- `corpus/**/case.json`
- Outside the dossier's `GENERATED` block
- `domain.md` / `profile.json`
- `PIPELINE.md` (only when changing the process)
- Project-specific `tools/` and `tools/INDEX.md`

---

## 8. Shortest paths

### Add a capability

```text
1. Add a key to state.json#features
2. cp capabilities/_TEMPLATE/README.md capabilities/<feature-id>/README.md
3. Declare capabilities in corpus/derived/<group>/<case>/case.json
4. python3 tools/capabilities/build_capability_index.py
5. python3 tools/capabilities/build_feature_dossiers.py
6. python3 tools/capabilities/validate_capability_ids.py
```

### Add a case

```text
1. Put the input in corpus/derived/<group>/<case>/
2. Write case.json and declare capabilities
3. Run build_capability_index.py
4. Add reference/target outputs to the dossier's Case table
```

### Change a capability verdict

```text
1. Change sourceStatus/effectStatus/refs in state.json#features
2. Edit notes outside the dossier's GENERATED block
3. Rebuild + validate
```

### Add a platform

```text
1. Copy profiles/_TEMPLATE.json
2. Fill platform/source_roots/reference_runtime/target_runtime/comparison/toolchains
3. Use bootstrap to generate a temporary workspace and verify it
```

---

## 9. Common anti-patterns

1. **Editing `index.json` directly**: the next build overwrites it and `state.json`
   still does not change.
2. **Keeping conclusions only in the chat**: the next session cannot find them.
3. **Mixing raw dumps and conclusions in `evidence/source/`**: impossible to search.
4. **Running one "big" case per branch**: differences cannot be attributed.
5. **Not writing `case.json` and guessing capabilities from directory names**: the
   generator does not guess.
6. **Treating `runs/regress-current/` as long-term evidence**: it can be overwritten
   at any time.
7. **Using historical directories as inputs**: `history/` and `runs/archive/` are
   frozen.

---

## 10. One-sentence summary

**The template fixes "input, evidence, case, implementation, run, conclusion" into a
set of traceable paths; `state.json` records state, `capabilities/` records the
ledger and the story, and `PIPELINE.md` records the process.**
