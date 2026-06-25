# TODO

## Execution Rules

- Prioritize real runtime functionality over artificial tests.
- Do not modify user-owned shell files without backup and validation.
- Any `doctor --fix` action must either create a backup before changing user files or prove manifest ownership before changing managed files.
- Do not mark an item completed without runtime verification.
- Do not silence errors just to make a verification pass.
- Do not modify tests to justify a functional change.
- If a verification cannot run, record the reason and risk in `PROGRESS.md`.
- If a critical bug appears while working an item, add it to this file before continuing.
- Update `PROGRESS.md` after every attempted item, including failures and partial work.
- Run `graphify update` after every completed item and record the result in `PROGRESS.md`.

## Phase 1 - Safe Config Writes

- [x] 01. Implement rotating backups before writing `.zshrc`
  - Impact: high
  - Verification: writing config creates a timestamped backup when `.zshrc` exists.

- [x] 02. Validate generated `.zshrc` with `zsh -n` before replacing the real file
  - Impact: high
  - Verification: invalid generated config does not replace the existing `.zshrc`.

- [x] 03. Add rollback support for failed config writes
  - Impact: high
  - Verification: failed apply restores the previous `.zshrc`.

- [x] 04. Add a manifest of files created or managed by Omega
  - Impact: high
  - Verification: apply records managed config, backups, and symlinked themes.

- [x] 05. Never touch files that Omega did not create or does not own
  - Impact: high
  - Verification: existing non-symlink theme/config files remain unchanged.

- [x] 05b. Make `install.sh` respect manifest ownership for theme symlinks
  - Impact: critical
  - Verification: install path delegates theme symlinks to `link_omega_themes()` instead of unlinking paths directly.

- [x] 06. Add atomic writes for `state.json`
  - Impact: high
  - Verification: interrupted write cannot leave partially written JSON.

- [x] 06b. Make installer binary symlinks ownership-safe
  - Impact: high
  - Verification: installer does not overwrite existing foreign `omega` or `oz` commands.

- [x] 07. Normalize and validate `state.json` schema
  - Impact: high
  - Verification: unknown fields are ignored and invalid field types fall back safely.

- [x] 08. Deduplicate and normalize selected plugin IDs
  - Impact: medium
  - Verification: duplicated plugin selections render once in `.zshrc`.

- [x] 08b. Normalize plugins imported from existing `.zshrc`
  - Impact: medium
  - Verification: duplicated plugins in imported `.zshrc` render once after Apply.

## Phase 2 - Doctor And Recovery

- [x] 09. Add `omega doctor` command
  - Impact: high
  - Verification: command reports zsh, git, OMZ, `.zshrc`, `$ZSH`, permissions, plugins, tools, and themes.

- [x] 10. Add `omega doctor --fix` for safe automatic repairs
  - Impact: high
  - Verification: safe fixes run only after backup and validation.

- [x] 10b. Report corrupt or invalid manifest in read-only doctor
  - Impact: high
  - Verification: `omega doctor` warns on corrupt or schema-invalid manifest without modifying it.

- [x] 11. Add clear diagnostics for missing Oh My Zsh
  - Impact: high
  - Verification: user gets actionable repair message instead of broken shell sourcing.

- [x] 12. Add clear diagnostics for missing selected binary tools
  - Impact: medium
  - Verification: doctor reports selected tools missing from PATH.

- [x] 13. Add clear diagnostics for missing external zsh plugins
  - Impact: medium
  - Verification: doctor reports selected external plugins not cloned.

- [x] 14. Integrate recovery actions with backups instead of only shell script cleanup
  - Impact: high
  - Verification: recovery can restore the latest valid backup.

## Phase 3 - Apply Flow Simplification

- [x] 15. Create `core/apply.py` as the single apply orchestrator
  - Impact: high
  - Verification: UI calls the orchestrator instead of doing filesystem work directly.

- [x] 16. Create pure `render_config(state, context)` flow
  - Impact: high
  - Verification: render can be executed without touching filesystem.

- [ ] 17. Separate install flow from apply flow
  - Impact: high
  - Verification: apply never installs packages; install never rewrites config unless requested.

- [x] 18. Add dry-run apply mode
  - Impact: medium
  - Verification: dry run shows intended file changes without writing them.

- [x] 19. Add config preview before writing `.zshrc`
  - Impact: medium
  - Verification: generated content can be inspected before replace.

- [x] 20. Return structured apply results instead of booleans
  - Impact: high
  - Verification: callers receive status, changed files, warnings, and errors.

## Phase 4 - Catalog And Installation

- [x] 21. Split zsh plugins from binary tools in the catalog
  - Impact: high
  - Verification: binary tools never render inside `plugins=(...)`.

- [x] 22. Add platform-aware package names to catalog
  - Impact: high
  - Verification: Debian/Termux package names resolve from catalog, not hardcoded branches.

- [x] 22b. Add Debian package override for `fortune`
  - Impact: medium
  - Verification: Debian/nala resolve `fortune` to `fortune-mod` before install.

- [x] 23. Add command detection names to catalog
  - Impact: medium
  - Verification: `bat/batcat`, `fd/fdfind`, and `ripgrep/rg` are handled by data.

- [ ] 24. Reject or warn on unknown plugin/tool IDs before rendering config
  - Impact: high
  - Verification: invalid state cannot produce invalid `.zshrc` silently.

- [ ] 25. Make `PluginInstaller.install_all()` return a structured result
  - Impact: medium
  - Verification: result includes installed, skipped, failed, and messages.

- [ ] 26. Add platform support flags per item
  - Impact: medium
  - Verification: unsupported tools are hidden or warned before install.

## Phase 5 - CLI And System Context

- [ ] 27. Remove duplicated system detection from `oz_tool.py`
  - Impact: medium
  - Verification: CLI uses shared core system stats/detection helpers.

- [ ] 28. Remove duplicated system detection from `DashboardScreen`
  - Impact: medium
  - Verification: dashboard uses shared core stats/detection helpers.

- [ ] 29. Make CLI commands thin wrappers around core services
  - Impact: medium
  - Verification: CLI contains presentation logic, not filesystem/business logic.

- [ ] 30. Add operation logs under `~/.omega-zsh/logs/`
  - Impact: medium
  - Verification: apply/install/doctor write separate logs.

## Phase 6 - TUI UX And Safety

- [ ] 31. Add first-run guided flow
  - Impact: medium
  - Verification: empty setup guides through OMZ, theme, tools, and apply.

- [ ] 32. Add safe minimal config mode
  - Impact: high
  - Verification: user can generate a minimal `.zshrc` with no visual/heavy commands.

- [ ] 33. Add Problems screen
  - Impact: medium
  - Verification: TUI lists current doctor findings and actions.

- [ ] 34. Add Restore Backup screen/action
  - Impact: high
  - Verification: user can choose and restore a previous `.zshrc` backup.

- [ ] 35. Mark UI items as installed, missing, unsupported, or unmanaged
  - Impact: medium
  - Verification: plugin/tool selectors show real status.

- [ ] 36. Add startup impact labels for plugins/tools
  - Impact: low
  - Verification: UI can show low/medium/high startup impact.

- [ ] 37. Add presets: Minimal, Fast, Pretty, Power User, Termux Safe
  - Impact: medium
  - Verification: selecting a preset updates state predictably.

- [ ] 38. Make expensive previews explicit instead of automatic on navigation
  - Impact: medium
  - Verification: theme/header previews run only by user action or debounced request.

## Phase 7 - Template And Script Cleanup

- [ ] 39. Reduce `personal.zsh.j2` to a minimal safe file
  - Impact: high
  - Verification: generated personal config has no surprise dashboard or opinionated functions by default.

- [ ] 40. Consider merging `personal.zsh` and `custom.zsh` into one user file
  - Impact: medium
  - Verification: user customization path is simpler and backward risk is documented.

- [ ] 41. Split `.zshrc.j2` into smaller template blocks
  - Impact: medium
  - Verification: OMZ, tools, header, and Termux sections can be rendered independently.

- [ ] 42. Reduce generated `.zshrc` comments to practical debug information
  - Impact: low
  - Verification: generated config is shorter and easier to read.

- [ ] 43. Convert `install.sh` into a minimal wrapper around Python logic
  - Impact: high
  - Verification: install logic lives in one Python path, shell only bootstraps.

- [ ] 44. Decide whether `Figlet_Fonts/` is demo code or product code
  - Impact: low
  - Verification: dead/demo code is removed or documented as optional tool.

- [ ] 45. Run final graphify update and architecture audit
  - Impact: high
  - Verification: `graphify update` completes and `GRAPH_REPORT.md` reflects the simplified architecture.
