# Progress

## Run Metadata

- Started: 2026-06-21
- Goal: make Omega-ZSH simpler, safer, and more robust.
- Policy: real runtime functionality over artificial tests.
- Audit files: `TODO.md`, `PROGRESS.md`, `graphify-out/`.

## Execution Rules

- No item is marked completed without runtime verification.
- Failures and partial work must be recorded, not hidden.
- Tests are not modified to justify code changes.
- If verification cannot run, the reason and residual risk are recorded.
- `graphify update` runs after every completed item.

## Log

### 2026-06-21 - Initialization

- TODO item: setup audit loop
- Status: completed
- Files changed:
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - Added an auditable backlog and progress protocol for future work.
- Verification commands:
  - Not applicable for documentation-only initialization.
- Verification result:
  - Files created.
- Graphify update:
  - Pending. Will run after first functional item completion.
- Risks:
  - None for runtime behavior.
- Next:
  - Start Item 01: rotating backups before writing `.zshrc`.

### 2026-06-21 - Item 01

- TODO item: `01. Implement rotating backups before writing .zshrc`
- Status: completed
- Files changed:
  - `omega_zsh/core/backup.py`
  - `omega_zsh/core/generator.py`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - `ConfigGenerator.generate_zshrc()` now creates a timestamped backup before replacing an existing `.zshrc`.
  - Backups are stored in `.omega-backups` next to the target file.
  - Only the newest 10 backups for `.zshrc` are kept.
  - No backup directory is created when there is no existing `.zshrc` to protect.
- Verification commands:
  - `python3 -m compileall omega_zsh`
  - Runtime smoke script covering first write, backup creation, backup content, and pruning to 10 backups.
- Verification result:
  - Passed: `backup_smoke: ok`.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 434 nodes, 710 edges, 21 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - Backup location is currently next to the target file. This is simple and local, but a future manifest may move or also record backups under `~/.omega-zsh`.
- Next:
  - Continue with Item 02: validate generated `.zshrc` with `zsh -n` before replacing the real file.

### 2026-06-21 - Item 02

- TODO item: `02. Validate generated .zshrc with zsh -n before replacing the real file`
- Status: completed
- Files changed:
  - `omega_zsh/core/shell.py`
  - `omega_zsh/core/generator.py`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - Generated `.zshrc` content is written to a temporary file first.
  - The temporary file is validated with `zsh -n` when `zsh` is available.
  - Invalid generated config is deleted and does not replace the existing `.zshrc`.
  - Backup creation happens only after validation passes.
- Verification commands:
  - `python3 -m compileall omega_zsh`
  - Runtime smoke script covering valid config replacement and invalid config preservation.
- Verification result:
  - Passed: `zsh_validation_smoke: ok`.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 439 nodes, 717 edges, 23 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - If `zsh` is not installed, validation is skipped so initial bootstrap flows are not blocked. This should be surfaced later by `omega doctor`.
- Next:
  - Continue with Item 03: rollback support for failed config writes.

### 2026-06-21 - Item 03

- TODO item: `03. Add rollback support for failed config writes`
- Status: completed
- Files changed:
  - `omega_zsh/core/backup.py`
  - `omega_zsh/core/generator.py`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - Added `restore_backup()` for restoring a backup over a target file.
  - If atomic replace fails during `.zshrc` generation, the temporary file is removed and the previous backup is restored.
  - Backup pruning now happens only after replacement succeeds.
- Verification commands:
  - `python3 -m compileall omega_zsh`
  - Runtime smoke script with mocked `os.replace` failure.
- Verification result:
  - Passed: `rollback_smoke: ok`.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 442 nodes, 723 edges, 21 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - Current rollback handles replacement failure. A future apply orchestrator should also validate post-write shell startup behavior and rollback if runtime load fails.
- Next:
  - Continue with Item 04: manifest of files managed by Omega.

### 2026-06-21 - Item 04

- TODO item: `04. Add a manifest of files created or managed by Omega`
- Status: completed
- Files changed:
  - `omega_zsh/core/manifest.py`
  - `omega_zsh/core/generator.py`
  - `omega_zsh/ui/app.py`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - Added `~/.omega-zsh/manifest.json` support through `core/manifest.py`.
  - Generated `.zshrc` files are recorded as managed config files.
  - Created backups are recorded as managed backup files with their source path.
  - Omega theme symlinks are recorded as managed theme symlinks with their source theme path.
- Verification commands:
  - `python3 -m compileall omega_zsh`
  - Runtime smoke script covering config entry, backup entry, and theme symlink entry in manifest.
- Verification result:
  - Passed: `manifest_smoke: ok`.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 450 nodes, 745 edges, 21 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - Manifest currently records ownership but does not yet enforce it. Enforcement belongs to Item 05.
- Next:
  - Continue with Item 05: never touch files Omega does not own.

### 2026-06-21 - Item 05

- TODO item: `05. Never touch files that Omega did not create or does not own`
- Status: completed
- Files changed:
  - `omega_zsh/core/manifest.py`
  - `omega_zsh/ui/app.py`
  - `scripts/uninstall.sh`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - Added manifest ownership helpers: `get_managed_file()`, `is_managed_file()`, `path_exists_or_is_symlink()`, and `require_managed_or_absent()`.
  - Theme symlink creation now refuses to overwrite/remove any existing path unless it is absent or registered in manifest as the expected Omega-managed `theme_symlink` with matching source metadata.
  - Existing foreign files are preserved.
  - Existing foreign symlinks are preserved.
  - Missing or corrupt manifest does not authorize replacement of existing paths.
  - Recovery/purge now preserves `~/.omega-zsh` by default, protecting manifest, state, backups, and future logs.
- Verification commands:
  - `python3 -m compileall omega_zsh`
  - Runtime smoke script covering foreign file preservation, foreign symlink preservation, corrupt manifest behavior, owned symlink replacement, and manifest recording.
  - `bash -n scripts/uninstall.sh`
  - Recovery dry-run smoke with `HOME=<tmp>` and `--dry-run --yes --purge`, asserting `~/.omega-zsh/manifest.json` remains present.
- Verification result:
  - Passed: `ownership_smoke: ok` and shell syntax check passed.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 455 nodes, 764 edges, 22 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - `~/.zshrc` is still a special case: Omega intentionally manages it with backup, validation, rollback, and manifest recording. Future apply orchestration should distinguish first-time adoption from already-managed config more explicitly.
  - Recovery currently preserves `~/.omega-zsh` entirely. A future purge-total mode may need a snapshot-before-delete flow if the user explicitly wants complete removal.
- Next:
  - Continue with Item 06: atomic writes for `state.json`.

### 2026-06-21 - Item 06

- TODO item: `06. Add atomic writes for state.json`
- Status: completed
- Files changed:
  - `omega_zsh/core/state.py`
  - `tests/test_state.py`
  - `tests/test_ui_apply.py`
  - `tests/test_ui_app.py`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - `StateManager.save()` now writes state to `state.tmp` first and atomically replaces `state.json`.
  - Existing UI apply tests were updated to match the current runtime behavior for safe `fastfetch` command generation and success notification text.
  - `link_omega_themes()` ownership behavior now has versioned test coverage for foreign file preservation, corrupt manifest behavior, and owned symlink replacement.
- Verification commands:
  - `python3 -m compileall omega_zsh`
  - Runtime smoke script covering atomic state save, absence of leftover `.tmp`, and successful reload.
  - `python3 -m compileall tests`
  - `python3 -m pytest -q` attempted conditionally.
- Verification result:
  - Passed: `state_atomic_smoke: ok`.
  - Passed: test files compiled successfully.
  - Pytest not executed because `pytest` is not installed in the current environment (`pytest unavailable; skipped pytest`).
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 469 nodes, 783 edges, 29 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - Full pytest suite execution remains pending until a dev environment with pytest is available.
  - `pyproject.toml` currently does not include pytest in dev dependencies by project choice, so this is recorded rather than silently fixed.
- Next:
  - Continue with Item 07: normalize and validate `state.json` schema.

### 2026-06-21 - Item 07

- TODO item: `07. Normalize and validate state.json schema`
- Status: completed
- Files changed:
  - `omega_zsh/core/state.py`
  - `tests/test_state.py`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - Added `normalize_app_state()` to convert untrusted JSON-like data into a safe `AppState`.
  - Unknown fields are ignored.
  - Invalid string fields fall back to defaults.
  - `selected_header` is restricted to `fastfetch`, `figlet`, `cowsay`, or `none`.
  - `selected_plugins` is always normalized to a list of non-empty strings.
  - `StateManager.load()` now normalizes loaded JSON instead of trusting type hints.
  - `StateManager.save()` normalizes before writing, preserving the atomic write path from Item 06.
- Verification commands:
  - `python3 -m compileall omega_zsh tests`
  - Runtime smoke script covering invalid types, invalid header, plugin cleanup, save normalization, and reload.
  - `python3 -m pytest -q tests/test_state.py` attempted conditionally.
- Verification result:
  - Passed: `state_schema_smoke: ok`.
  - Passed: Python/test compile checks.
  - Pytest unavailable in the current interpreter, but `pytest` is declared in the `.[dev]` extra.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 480 nodes, 803 edges, 26 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - Plugin deduplication and catalog validation remain intentionally deferred to Item 08 and later catalog work.
- Next:
  - Continue with Item 08: deduplicate and normalize selected plugin IDs.

### 2026-06-21 - Item 08

- TODO item: `08. Deduplicate and normalize selected plugin IDs`
- Status: completed
- Files changed:
  - `omega_zsh/core/state.py`
  - `tests/test_state.py`
  - `tests/test_figlet.py`
  - `tests/test_oz.py`
  - `tests/test_ui_header_preview.py`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - `selected_plugins` normalization now strips whitespace, lowercases IDs, filters non-string/empty values, deduplicates while preserving first-seen order, and keeps catalog validation deferred to Item 24.
  - Full pytest drift was resolved after installing `.[dev]` in a temporary venv.
  - Figlet command tests now reflect runtime shell guards for `figlet`/`lolcat`.
  - `oz_tool` tests now patch `StateManager` instead of removed `state_manager` global.
  - Header preview tests now call the `@work`-wrapped method body directly via `__wrapped__`, avoiding old Textual `run_test(initial_screen=...)` API drift.
- Verification commands:
  - `python3 -m compileall omega_zsh tests`
  - Runtime smoke script covering plugin normalization, dedupe, order preservation, save, and reload.
  - `python3 -m pip install -e ".[dev]"` attempted globally and rejected by PEP 668, as expected on this system.
  - Temporary venv: `/tmp/opencode/omega-zsh-test-venv/bin/python -m pip install -e ".[dev]"`.
  - Temporary venv: `/tmp/opencode/omega-zsh-test-venv/bin/python -m pytest -q`.
- Verification result:
  - Passed: `plugin_dedupe_smoke: ok`.
  - Passed: Python/test compile checks.
  - Passed: full pytest suite in temporary venv: `64 passed`.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 487 nodes, 815 edges, 26 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - Unknown plugin IDs are still allowed intentionally; rejecting or warning on unknown IDs remains Item 24.
  - Temporary venv under `/tmp/opencode` is not part of the repo and can be discarded.
- Next:
  - Continue with Item 09: add `omega doctor` command.

### 2026-06-21 - Item 08b

- TODO item: `08b. Normalize plugins imported from existing .zshrc`
- Status: completed
- Files changed:
  - `omega_zsh/core/state.py`
  - `omega_zsh/ui/app.py`
  - `tests/test_state.py`
  - `tests/test_ui_apply.py`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - `_import_from_zshrc()` now returns a normalized `AppState`, so duplicated or mixed-case plugins imported from an existing `.zshrc` are cleaned before use.
  - `OmegaApp.save_state()` now stores the normalized state in memory before writing it, so Apply uses the same cleaned state that is persisted.
  - Plugin normalization now treats quoted empty tokens such as `""` or `''` as empty and drops them.
- Verification commands:
  - `python3 -m compileall omega_zsh tests`
  - Runtime smoke script covering duplicated/mixed-case plugins imported from `.zshrc`.
  - `/tmp/opencode/omega-zsh-test-venv/bin/python -m pytest -q`
- Verification result:
  - Passed: `zshrc_import_dedupe_smoke: ok`.
  - Passed: full pytest suite in temporary venv: `65 passed`.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 489 nodes, 820 edges, 24 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - Unknown plugin IDs are still allowed intentionally; rejecting or warning on unknown IDs remains Item 24.
- Next:
  - Continue with Item 09: add `omega doctor` command.

### 2026-06-24 - Item 09

- TODO item: `09. Add omega doctor command`
- Status: completed
- Files changed:
  - `omega_zsh/core/doctor.py`
  - `omega_zsh/cli/oz_tool.py`
  - `tests/test_doctor.py`
  - `tests/test_oz.py`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - Added `run_doctor()` as a read-only core diagnostic service.
  - `omega doctor`, `omega doc`, `oz doctor`, and `oz doc` now render a Rich diagnostics table through the existing CLI delegation path.
  - Doctor reports `zsh`, `git`, Oh My Zsh, resolved `$ZSH`, `.zshrc`, Omega/state directory writability, `.zshrc` directory writability, manifest availability, selected binary tools, selected external plugins, and selected theme availability.
  - Doctor returns structured checks with `id`, `status`, `severity`, `message`, and `detail` so future UI or repair flows can consume the same result.
  - No repair or filesystem mutation is performed by doctor.
- Verification commands:
  - `python3 -m compileall omega_zsh tests`
  - `/tmp/opencode/omega-zsh-test-venv/bin/python -m pytest -q`
  - `HOME="/tmp/opencode/omega-doctor-smoke" ZSH="/tmp/opencode/omega-doctor-smoke/.oh-my-zsh" /tmp/opencode/omega-zsh-test-venv/bin/python -m omega_zsh doctor`
- Verification result:
  - Passed: Python/test compile checks.
  - Passed: full pytest suite in temporary venv: `68 passed`.
  - Passed: CLI smoke rendered `OMEGA DOCTOR (WARNING)` and reported expected checks for the temporary installation.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 509 nodes, 881 edges, 24 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - Permission checks use effective `os.access()` and do not attempt writes; this is intentional for read-only doctor but may miss filesystem edge cases that only appear during apply.
  - Binary tool detection currently uses plugin ID as command name. Catalog aliases such as distro-specific command names remain deferred to Item 23.
  - Doctor is diagnostic only; safe repair remains Item 10.
- Next:
  - Continue with Item 10: add `omega doctor --fix` for safe automatic repairs.

### 2026-06-24 - Item 09 Review Follow-up

- TODO item: `09. Add omega doctor command`
- Status: completed
- Files changed:
  - `omega_zsh/core/doctor.py`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - Cached `zsh` and `git` command lookups inside `run_doctor()` instead of calling `which()` repeatedly.
  - Cached repeated permission and theme existence checks inside one doctor run.
  - Added an execution rule for Item 10: every `doctor --fix` action must either back up user files before changing them or prove manifest ownership before changing managed files.
- Verification commands:
  - `python3 -m compileall omega_zsh tests`
  - `/tmp/opencode/omega-zsh-test-venv/bin/python -m pytest -q`
  - `HOME="/tmp/opencode/omega-doctor-smoke" ZSH="/tmp/opencode/omega-doctor-smoke/.oh-my-zsh" /tmp/opencode/omega-zsh-test-venv/bin/python -m omega_zsh doctor`
- Verification result:
  - Passed: Python/test compile checks.
  - Passed: full pytest suite in temporary venv: `68 passed`.
  - Passed: CLI smoke rendered the doctor report successfully.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 510 nodes, 882 edges, 25 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - No intended runtime behavior change beyond removing repeated lookups.
- Next:
  - Run verification, update graph, then continue with Item 10.

### 2026-06-21 - Item 07 Edge Hardening

- TODO item: `07. Normalize and validate state.json schema`
- Status: completed
- Files changed:
  - `omega_zsh/core/state.py`
  - `tests/test_state.py`
  - `PROGRESS.md`
- Behavior changed:
  - `StateManager.load()` now passes raw JSON data directly to `normalize_app_state()` instead of calling `.items()` first.
  - Valid JSON that is not an object, such as a list, now resolves to safe defaults instead of falling through to `.zshrc` import.
  - `selected_header` now passes through `_clean_string()` before membership validation, avoiding unhashable-type crashes and accepting trimmed values such as `" none "`.
- Verification commands:
  - `python3 -m compileall omega_zsh tests`
  - Runtime smoke script covering non-dict JSON, non-hashable header value, and trimmed header value.
  - `python3 -m pytest -q tests/test_state.py` attempted conditionally.
- Verification result:
  - Passed: `state_schema_edge_smoke: ok`.
  - Passed: Python/test compile checks.
  - Pytest unavailable in the current interpreter, but `pytest` is declared in the `.[dev]` extra.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 484 nodes, 809 edges, 28 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - Plugin deduplication remains deferred to Item 08.
- Next:
  - Continue with Item 08: deduplicate and normalize selected plugin IDs.

### 2026-06-21 - Item 06b

- TODO item: `06b. Make installer binary symlinks ownership-safe`
- Status: completed
- Files changed:
  - `install.sh`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - Added `safe_link_bin()` to avoid overwriting existing foreign `omega` or `oz` commands.
  - Installer now creates `omega`/`oz` symlinks only when absent or already pointing to the expected Omega virtualenv executable.
  - Installer records verified binary symlinks in `~/.omega-zsh/manifest.json` as `bin_symlink` entries.
- Verification commands:
  - `bash -n install.sh`
  - `python3 -m compileall omega_zsh tests`
  - Runtime smoke script extracting `safe_link_bin()` and verifying foreign symlink preservation plus missing symlink creation.
- Verification result:
  - Passed: install script syntax check.
  - Passed: Python/test compile checks.
  - Passed: binary symlink smoke preserved a foreign `omega` symlink and created an Omega-owned `oz` symlink.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 472 nodes, 787 edges, 27 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - `install.sh` still carries complex shell bootstrap logic and string commands. Full simplification remains under Item 43.
  - Manifest recording of bin symlinks happens after link creation; future core installer flow should own this end-to-end in Python.
- Next:
  - Continue with Item 07: normalize and validate `state.json` schema.

### 2026-06-21 - Item 05b / Audit Drift Fixes

- TODO item: `05b. Make install.sh respect manifest ownership for theme symlinks`
- Status: completed
- Files changed:
  - `install.sh`
  - `omega_zsh/assets/templates/.zshrc.j2`
  - `pyproject.toml`
  - `tests/test_context.py`
  - `TODO.md`
  - `PROGRESS.md`
- Behavior changed:
  - `install.sh` no longer manually unlinks/recreates Omega theme symlinks.
  - Installer theme sync now delegates to `link_omega_themes(ctx.assets_dir, ctx.omz_dir, default_manifest_path(ctx.home))`, preserving Item 05 ownership rules.
  - `run_with_spinner()` no longer uses `eval "$cmd"`; it runs commands through `bash -c "$cmd"` to avoid an extra eval expansion layer.
  - Installer no longer uninstalls global pip `lolcat`; it warns and leaves global packages untouched.
  - `.zshrc.j2` now quotes `zcompile` paths safely via `zsh -c 'zcompile "$1"' -- "$zfile"`.
  - `pytest>=8.0.0` was added to the dev extra so documented test commands are installable.
  - Obsolete singleton expectation in `tests/test_context.py` was replaced with independent-context behavior.
- Verification commands:
  - Grep audit for removed stale patterns: `os.unlink`, `eval "$cmd"`, `pip3 uninstall`, old fastfetch/notify expectations, and singleton assertion.
  - `bash -n install.sh`
  - `bash -n scripts/uninstall.sh`
  - `python3 -m compileall omega_zsh tests`
  - Runtime smoke script covering installer-equivalent theme sync with foreign file preservation and owned symlink replacement.
  - Rendered `.zshrc` validation with `zsh -n`.
  - `python3 -m pytest -q` attempted conditionally.
- Verification result:
  - Passed: stale pattern grep returned no matches.
  - Passed: shell syntax checks.
  - Passed: Python/test compile checks.
  - Passed: `install_manifest_smoke: ok`.
  - Passed: rendered `.zshrc` syntax validation.
  - Pytest still unavailable in the current interpreter, but `pytest` is now declared in `.[dev]`.
- Graphify update:
  - Command: `graphify update`
  - Result: passed. Rebuilt code graph with 470 nodes, 784 edges, 24 communities; updated `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md`.
- Risks:
  - `run_with_spinner()` still accepts command strings for complex bootstrap commands. Full conversion to array-based or Python-owned install flow remains under Item 43.
  - Importing `link_omega_themes()` from `omega_zsh.ui.app` works because Textual is a runtime dependency, but a future refactor should move theme sync to a core module.
- Next:
  - Continue with Item 07: normalize and validate `state.json` schema.
