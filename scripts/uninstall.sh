#!/usr/bin/env bash
# Safe uninstaller for omega-zsh-python / omega-zsh.
# Usage: bash scripts/uninstall.sh [--dry-run] [--yes] [--purge] [--no-backup]

set -Eeuo pipefail

DRY_RUN=false
ASSUME_YES=false
PURGE=false
DO_BACKUP=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --yes|-y) ASSUME_YES=true ;;
    --purge) PURGE=true ;;
    --no-backup) DO_BACKUP=false ;;
    --help|-h)
      cat <<'EOF'
Usage:
  bash scripts/uninstall.sh [options]

Options:
  --dry-run      Simulate uninstall without changing files.
  --yes, -y      Skip confirmation prompts.
  --purge        Search extra Omega-related paths and offer to remove them.
  --no-backup    Do not create backups before editing shell files.
  --help, -h     Show this help.
EOF
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

C_RESET='\033[0m'
C_OK='\033[1;32m'
C_WARN='\033[1;33m'
C_ERR='\033[1;31m'
C_INFO='\033[1;34m'
C_DIM='\033[2m'

log() { printf "%b\n" "${C_INFO}[i]${C_RESET} $*"; }
ok() { printf "%b\n" "${C_OK}[✓]${C_RESET} $*"; }
warn() { printf "%b\n" "${C_WARN}[!]${C_RESET} $*"; }
err() { printf "%b\n" "${C_ERR}[x]${C_RESET} $*" >&2; }
dry() { printf "%b\n" "${C_DIM}[dry-run]${C_RESET} $*"; }

BACKUP_ROOT="$HOME/.omega-zsh-uninstall-backup/$(date +%Y%m%d-%H%M%S)"
OMEGA_RE='omega[-_]?zsh|omega_zsh|omegazsh|omega-zsh-python'

CONFIG_FILES=(
  "$HOME/.zshrc"
  "$HOME/.bashrc"
  "$HOME/.profile"
  "$HOME/.bash_profile"
)

CANDIDATE_DIRS=(
  "$HOME/.omega-zsh"
  "$HOME/.omega_zsh"
  "$HOME/.config/omega-zsh"
  "$HOME/.config/omega_zsh"
  "$HOME/.cache/omega-zsh"
  "$HOME/.cache/omega_zsh"
  "$HOME/.local/share/omega-zsh"
  "$HOME/.local/share/omega_zsh"
  "$HOME/omega-zsh"
  "$HOME/omega-zsh-python"
)

CANDIDATE_BINS=(
  "$HOME/.local/bin/omega"
  "$HOME/.local/bin/omega-zsh"
  "$HOME/.local/bin/omegazsh"
  "$HOME/.local/bin/omega-zsh-python"
)

if [[ -n "${PREFIX:-}" ]]; then
  CANDIDATE_BINS+=(
    "$PREFIX/bin/omega"
    "$PREFIX/bin/omega-zsh"
    "$PREFIX/bin/omegazsh"
    "$PREFIX/bin/omega-zsh-python"
  )
  CANDIDATE_DIRS+=(
    "$PREFIX/share/omega-zsh"
    "$PREFIX/share/omega_zsh"
    "$PREFIX/etc/omega-zsh"
    "$PREFIX/etc/omega_zsh"
  )
fi

confirm() {
  local prompt="${1:-Continue?}"
  [[ "$ASSUME_YES" == true ]] && return 0
  printf "%b" "${C_WARN}[?]${C_RESET} $prompt [y/N]: "
  read -r answer
  case "${answer,,}" in y|yes|s|si|sí) return 0 ;; *) return 1 ;; esac
}

backup_file() {
  local file="$1"
  [[ "$DO_BACKUP" == true && -f "$file" ]] || return 0
  if [[ "$DRY_RUN" == true ]]; then
    dry "Back up $file into $BACKUP_ROOT"
    return 0
  fi
  mkdir -p "$BACKUP_ROOT"
  local safe_name
  safe_name="$(printf "%s" "$file" | sed 's#/#__#g')"
  cp -p "$file" "$BACKUP_ROOT/$safe_name"
  ok "Backup created: $BACKUP_ROOT/$safe_name"
}

remove_path() {
  local target="$1"
  [[ -e "$target" || -L "$target" ]] || return 0
  log "Removing: $target"
  if [[ "$DRY_RUN" == true ]]; then
    dry "rm -rf -- $target"
  else
    rm -rf -- "$target"
    ok "Removed: $target"
  fi
}

clean_shell_file() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  grep -Eiq "$OMEGA_RE" "$file" || return 0

  log "Omega references found in: $file"
  backup_file "$file"

  if [[ "$DRY_RUN" == true ]]; then
    dry "Remove Omega blocks/lines from $file"
    grep -Ein "$OMEGA_RE" "$file" || true
    return 0
  fi

  local tmp
  tmp="$(mktemp)"

  awk '
    BEGIN { skip = 0 }
    /^[[:space:]]*#?[[:space:]]*>>>[[:space:]]*(omega[-_]?zsh|omega_zsh|omegazsh|omega-zsh-python)/ { skip = 1; next }
    /^[[:space:]]*#?[[:space:]]*<<<[[:space:]]*(omega[-_]?zsh|omega_zsh|omegazsh|omega-zsh-python)/ { skip = 0; next }
    skip == 1 { next }
    tolower($0) ~ /(omega[-_]?zsh|omega_zsh|omegazsh|omega-zsh-python)/ { next }
    { print }
  ' "$file" > "$tmp"

  cat "$tmp" > "$file"
  rm -f "$tmp"
  ok "Cleaned: $file"
}

detect_python() {
  if command -v python >/dev/null 2>&1; then
    printf 'python'
  elif command -v python3 >/dev/null 2>&1; then
    printf 'python3'
  else
    return 1
  fi
}

uninstall_pip_packages() {
  local py packages
  py="$(detect_python 2>/dev/null || true)"
  [[ -n "$py" ]] || return 0

  packages="$($py -m pip list --format=freeze 2>/dev/null | grep -Ei '^(omega-zsh|omega_zsh|omegazsh|omega-zsh-python)=' || true)"
  [[ -n "$packages" ]] || return 0

  log "Related pip packages detected:"
  printf "%s\n" "$packages"

  while IFS='=' read -r pkg _version; do
    [[ -n "$pkg" ]] || continue
    if [[ "$DRY_RUN" == true ]]; then
      dry "$py -m pip uninstall -y $pkg"
    else
      "$py" -m pip uninstall -y "$pkg" || warn "Could not uninstall pip package: $pkg"
    fi
  done <<< "$packages"
}

clean_extra_purge_paths() {
  [[ "$PURGE" == true ]] || return 0
  warn "Purge mode enabled: searching extra Omega-related paths."

  local roots=("$HOME/.config" "$HOME/.cache" "$HOME/.local/share" "$HOME/.local/bin")
  [[ -n "${PREFIX:-}" ]] && roots+=("$PREFIX/bin" "$PREFIX/share" "$PREFIX/etc")

  local found=()
  for root in "${roots[@]}"; do
    [[ -d "$root" ]] || continue
    while IFS= read -r path; do
      found+=("$path")
    done < <(find "$root" -maxdepth 2 \( -iname '*omega-zsh*' -o -iname '*omega_zsh*' -o -iname '*omegazsh*' \) 2>/dev/null)
  done

  [[ "${#found[@]}" -gt 0 ]] || { ok "No extra purge paths found."; return 0; }

  printf "\nExtra paths detected:\n"
  printf "  - %s\n" "${found[@]}"
  printf "\n"

  if confirm "Remove these extra paths?"; then
    for path in "${found[@]}"; do remove_path "$path"; done
  else
    warn "Skipped extra purge cleanup."
  fi
}

cat <<EOF

${C_INFO}OMEGA-ZSH UNINSTALLER${C_RESET}

This script will try to:
  1. Remove Omega references from shell files.
  2. Remove known Omega launchers/binaries.
  3. Remove known Omega config/cache/data directories.
  4. Uninstall related pip packages, if present.

It will not remove zsh, oh-my-zsh, powerlevel10k, or external themes.

EOF

[[ "$DRY_RUN" == true ]] && warn "Dry-run mode enabled: no changes will be made."
[[ "$PURGE" == true ]] && warn "Purge mode enabled: extra Omega paths will be searched."
[[ "$DO_BACKUP" == true ]] && log "Backups will be stored in: $BACKUP_ROOT" || warn "Backups disabled."

if ! confirm "Start Omega ZSH uninstall?"; then
  warn "Operation cancelled."
  exit 0
fi

log "Cleaning shell files..."
for file in "${CONFIG_FILES[@]}"; do clean_shell_file "$file"; done

log "Removing known launchers/binaries..."
for bin in "${CANDIDATE_BINS[@]}"; do remove_path "$bin"; done

log "Removing known Omega directories..."
for dir in "${CANDIDATE_DIRS[@]}"; do remove_path "$dir"; done

log "Checking related pip packages..."
uninstall_pip_packages

clean_extra_purge_paths

ok "Uninstall finished."
[[ "$DRY_RUN" != true && "$DO_BACKUP" == true && -d "$BACKUP_ROOT" ]] && log "Backup saved at: $BACKUP_ROOT"

cat <<'EOF'

Recommended next step:
  Restart your terminal or run:

    exec $SHELL -l

If something looks wrong, restore your shell files from the backup.

EOF
