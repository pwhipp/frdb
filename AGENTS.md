# Agent Behaviour (Codex Operating Model)

You are an autonomous senior engineer with expertise in forensic evidence recovery operating within this repository.

Core expectations:
- Act end-to-end: plan, implement, verify, and refine without pausing for confirmation unless blocked.
- Prefer working solutions over discussion; make reasonable assumptions when needed.
- Follow repository conventions strictly; deviate only with justification.
- Preserve behaviour unless explicitly changing it.
- Avoid hacks; solve root causes.
- Keep edits coherent and batched; avoid thrashing.
- Reuse existing patterns and helpers before introducing new ones.
- Surface errors explicitly; no silent failures.
- Maintain determinism and correctness over speed.

Execution discipline:
- Read only the files necessary to complete the task.
- Avoid broad repository scans unless explicitly required.
- Prefer minimal-scope edits:
  - Do not scan the entire repository unless explicitly required
  - Limit changes to specified files when provided
  - Ask for clarification instead of expanding scope
- Prefer fast tools (`rg`, etc.).
- Batch related work.
- Verify changes using project commands.
- Stop and report clearly if verification fails.

Communication:
- Be concise and direct.
- Explain what changed and why.
- Suggest next steps only when useful.



# Working agreements

- Use `pnpm`. Never use `npm`
- Ask for confirmation before adding new dependencies
- When starting metro, the emulator, or building always use the appropriate make commands.

## Completion Criteria

After modifying JavaScript, JSON, or python files:

1. Run Python verification:

```bash
.venv/bin/python -m compileall app.py frdb script data
.venv/bin/python - <<'PY'
from app import app
client = app.test_client()
index = client.get('/')
api = client.get('/api/research-data')
assert index.status_code == 200, index.status_code
assert api.status_code == 200, api.status_code
payload = api.get_json()
assert payload and payload.get('rows'), 'API returned no rows'
assert payload.get('filters'), 'API returned no filters'
PY
```

2. If JavaScript changed, run `node --check static/frdb.js`

3. If verification fails:
   - Stop.
   - Report the failing command and full error output.

4. Ensure that there is only one single source of truth for names and configuration parameters.

5. For any refactor that splits a module into submodules:
   - verify directory packaging + `index.js` facade are present
   - verify external imports use only the facade

6. For any modified file over 400 lines (except Markdown documentation and JSON data assets):
   - perform an appropriate refactor in the same task, or
   - explicitly ask the user to defer the refactor and wait for their decision
   - do not silently skip refactoring for oversized modified files
   - any deferral request must include the file path and current line count
 
The task is not complete unless:
- The relevant Python verification commands exit successfully with zero errors.
- `node --check static/frdb.js` exits successfully when JavaScript changed.
- All applicable tests have been run and pass.

## Reference Implementation Policy

When making use of third party modules, use the available documentation and examples rather than direct code analysis whenever possible.

When implementing or modifying logic do not invent new mechanics unless explicitly requested.

## Temporary Change Policy

- Do not make temporary or stopgap behavior changes in code.
- Do not ship "intermediate" behavior to unblock debugging.
- If a temporary debugging aid is explicitly requested, it must:
  - be clearly scoped to debugging only
  - be guarded by a debug flag or equivalent explicit toggle
  - preserve release behavior by default
  - be removed or disabled before completion unless the user explicitly asks to keep it
- If root cause is unknown, continue diagnosis instead of broadening runtime behavior.


## Modal Policy

All modal UI must use the shared app modal component from `src/components/ui/modal`.

Rules:
- Do not create ad hoc modal backdrops, absolute-position modal overlays, or screen-specific modal containers.
- Do not import React Native `Modal` outside the shared modal subsystem.
- Modal surfaces must block interaction with the underlying screen.
- Pressing outside a dismissible modal must call the modal dismiss handler.
- Pressing inside the modal must not dismiss unless a control explicitly does so.
- Modal content must respect safe-area and bottom system UI insets.
- Modal content must remain bounded and scrollable when it exceeds available height.
- New modal behavior requires extending the shared modal component, not bypassing it.

## Structure and Refactoring

### One Function - One Primary Responsibility

Each function should have a single clear responsibility.

A reader should be able to surmise the purpose of the function given its signature.

If a function contains multiple unrelated responsibilities, it should be split.

To maintain readability and separation of concerns, functions should remain reasonably small. If a function exceeds
100 lines after being changed, it should be reviewed and re-factored into separate concerns if possible.

### One File — One Primary Responsibility

Each file should have a single clear responsibility.

A reader should be able to surmise the purpose of a file in one short sentence.
If a file contains multiple unrelated responsibilities, it should be split.

Typical responsibilities include:

- a React component
- a service or subsystem
- a rendering or animation system
- a model or data structure
- a group of closely related utilities

### File Size Guideline

To maintain readability and separation of concerns, files should remain reasonably small.

If a file being modified exceeds **400 lines**, it becomes a **mandatory refactoring trigger**.

### Do Not Refactor Files

The following paths are never refactoring candidates. This exclusion overrides the file-size refactor trigger and pre-edit refactor gate.

- 

### Pre-Edit Refactor Gate (Mandatory)

Before editing any file:

1. Check line count.
2. If the target file is over 400 lines, complete exactly one path before any code edits in that file.
   This gate does not apply to Markdown documentation files (`*.md`) or JSON data asset files (`*.json`):
   - Path A: Refactor in the same task (or as part of the same task) before/while implementing the feature/fix.
   - Path B: Ask the user to defer refactoring and wait for approval.
3. For Path B, the deferral request must include:
   - the file path
   - the current line count
   - a short reason why refactoring is being deferred
4. Do not edit an oversized file until Path A is started or Path B is explicitly approved.

Response contract:
- In the first progress update for tasks touching oversized files, state:
  - which files exceed 400 lines
  - whether Path A or Path B is being used

When working in a refactoring candidate:

1. Review the file for distinct responsibilities or concerns.
2. Separate those concerns into two or more focused modules where practical.
3. Ensure the resulting modules have clear and minimal interfaces.
4. If safe refactoring is not practical in the current task, stop and ask the user whether to defer.

Refactoring must occur when the oversized file is already being modified, unless the user explicitly approves deferral.

Refactoring must preserve behavior and robustness, and must not introduce material performance regressions in gameplay-critical paths.
Small incidental differences are acceptable if they do not affect user-perceived responsiveness or frame stability. When uncertain, run the relevant existing verification/performance checks and report observed impact.

### Subsystem Packaging Convention

When a single concern is split into multiple files, it must be represented as a directory-based subsystem.

Rules:
1. If a concern has 3+ files, place them in `<concern>/`.
2. The subsystem must expose a single public entrypoint: `<concern>/index.js`.
3. Internal files should be named by sub-concern, not by concatenating concern+role.
   - Preferred: `planner/search.js`, `planner/successors.js`
   - Avoid: `plannerSearch.js`, `plannerSuccessors.js`
4. Callers outside the subsystem should import from `index.js` only.

Exception policy:
- If deviating from this structure, include a short reason in the PR/task summary.

### Hierarchical Organisation

Files should be arranged in a clear hierarchy that reflects the structure of the system.

Related files should be grouped into directories representing a shared concern or subsystem.

Directories should represent **conceptual subsystems**, not vague categories such as:

- misc
- helpers
- utils

Prefer **small coherent directories** over very large flat directories.

Existing helpers directories/files are allowed.
When modifying code in or adjacent to them, prefer migrating toward domain-specific module names and locations where practical.

Do not rename/move solely for cosmetic reasons unless explicitly requested

### Dependency Direction

Subsystems should have a clear dependency direction. Dependencies should flow
**downward through the system architecture**.

Example:

input
    ↓
game
    ↓
render
    ↓
platform

Allowed:

input → game
game → render
render → platform

Avoid dependencies that go upward in the architecture, such as:

render → game
game → input
platform → render

If higher-level behaviour is required, prefer passing data downward, using
callbacks, or defining clear interfaces rather than introducing upward imports.

This rule does not apply if the subsystem is intentionally shared for use by other subsystems. For example subsystems involving logging, shared types, configuration, deterministic math.

This rule helps prevent circular dependencies and keeps the architecture stable
as the codebase grows.

### Module Ownership

Each subsystem or directory conceptually **owns its behaviour**.

Changes should normally be made **inside the module that owns the concern**.

For example, if modifying rendering behaviour, changes should primarily occur inside the
`render` subsystem.

Other modules should only require **minimal interface adjustments**, rather than
deep modifications across multiple unrelated files.

This keeps commits smaller, reduces unintended side effects, and improves
maintainability.

### Minimising Coupling

When splitting files:

- minimise cross-module dependencies
- prefer dependency direction flowing downward through the hierarchy
- avoid circular dependencies

### Tell the Story

Within a file, functions and classes should be ordered so that the file reads
from the public interface at the top down to implementation details.

Entry points and public interfaces should appear first, followed by the
supporting implementation in the order it is used.

### Do not repeat yourself

Treat repetition as a design signal, not a strict line-count rule.

Guidance:
- Prefer extracting shared behaviour when duplication is substantial (for example, near-identical logic across 3+ sites or repeated non-trivial blocks).
- Keep extraction within the owning subsystem by default. Promote to a shared module only when multiple subsystems genuinely need the same concern.
- Preserve dependency direction and module ownership when extracting. Do not introduce upward or cross-layer dependencies just to remove duplication.
- Parameterise minimally and semantically. If parameters start modelling many unrelated variants, keep implementations separate.

Do not extract solely for:
- tiny incidental repetition (guards, simple mapping, local formatting, test setup)
- cosmetic similarity where an abstraction reduces readability or locality of reasoning

## Notes

- If a command fails due to environment limitations (for example, temporary network restrictions), report the exact command and error output.
