# Omega Config Files

Omega currently keeps two user customization files:

- `~/.omega-zsh/personal.zsh`: generated only when absent and intended for structured data such as explicit paths, environment variables, and aliases.
- `~/.omega-zsh/custom.zsh`: created only when absent and intended for free-form manual shell customizations.

## Decision

Do not merge `personal.zsh` and `custom.zsh` yet.

## Rationale

Both paths are already generated and sourced by `.zshrc`. Merging them would require moving or rewriting user-owned shell content, which conflicts with Omega's safety rule unless a migration path has backup, validation, and explicit user consent.

Keeping both files is less surprising for existing users:

- Existing `personal.zsh` content remains untouched.
- Existing `custom.zsh` content remains untouched.
- New generated `personal.zsh` files are now minimal and contain only explicit user data.
- Free-form user logic still has a stable place in `custom.zsh`.

## Future Migration Requirements

If these files are merged later, the migration must:

- Create backups of both source files.
- Validate the merged shell file with `zsh -n` before replacing anything.
- Preserve ownership in the Omega manifest.
- Require an explicit user action; no automatic merge during read-only flows.
- Keep rollback available if validation or replacement fails.
