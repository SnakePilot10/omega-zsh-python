#!/usr/bin/env bash
# Safe uninstaller and nuclear shell fixer for omega-zsh-python / omega-zsh.
# Usage: bash scripts/uninstall.sh [--dry-run] [--yes] [--purge] [--nuclear-fix] [--no-backup]

set -Eeuo pipefail

DRY_RUN=false
ASSUME_YES=false
PURGE=false
DO_BACKUP=true
NUCLEAR_FIX=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --yes|-y) ASSUME_YES=true ;;
    --purge) PURGE=true ;;
    --nuclear-fix) NUCLEAR_FIX=true ;;
    --no-backup) DO_BACKUP=false ;;
    --help|-h)
      cat <<'EOF'
Usage:
  bash scripts/uninstall.sh [options]

Options:
  --dry-run       Simulate uninstall/fix without changing files.
  --yes, -y       Skip confirmation prompts.
  --purge         Search extra Omega-related paths and offer to remove them.
  --nuclear-fix   Rebuild broken shell startup files with minimal safe defaults.
  --no-backup     Do not create recovery backups.
  --help, -h      Show this help.

Examples:
  bash scripts/uninstall.sh --dry-run
  bash scripts/uninstall.sh
  bash scripts/uninstall.sh --nuclear-fix
  bash scripts/uninstall.sh --yes --purge --nuclear-fix
EOF
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

C_RESET='\033[0m'; C_OK='\033[1;32m'; C_WARN='\033[1;33m'; C_ERR='\033[1;31m'; C_INFO='\033[1;34m'; C_DIM='\033[2m'
log() { printf "%b\n" "${C_INFO}[i]${C_RESET} $*"; }
ok() { printf "%b\n" "${C_OK}[✓]${C_RESET} $*"; }
warn() { printf "%b\n" "${C_WARN}[!]${C_RESET} $*"; }
err() { printf "%b\n" "${C_ERR}[x]${C_RESET} $*" >&2; }
dry() { printf "%b\n" "${C_DIM}[dry-run]${C_RESET} $*"; }

RECOVERY_DIR="$HOME/.omega-zsh-recovery"
OMEGA_RE='omega[-_]?zsh|omega_zsh|omegazsh|omega-zsh-python'

CONFIG_FILES=("$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile" "$HOME/.bash_profile")
CANDIDATE_DIRS=(
  "$HOME/.omega-zsh" "$HOME/.omega_zsh" "$HOME/.config/omega-zsh" "$HOME/.config/omega_zsh"
  "$HOME/.cache/omega-zsh" "$HOME/.cache/omega_zsh" "$HOME/.local/share/omega-zsh" "$HOME/.local/share/omega_zsh"
  "$HOME/omega-zsh" "$HOME/omega-zsh-python"
)
CANDIDATE_BINS=("$HOME/.local/bin/omega" "$HOME/.local/bin/omega-zsh" "$HOME/.local/bin/omegazsh" "$HOME/.local/bin/omega-zsh-python")

if [[ -n "${PREFIX:-}" ]]; then
  CANDIDATE_BINS+=("$PREFIX/bin/omega" "$PREFIX/bin/omega-zsh" "$PREFIX/bin/omegazsh" "$PREFIX/bin/omega-zsh-python")
  CANDIDATE_DIRS+=("$PREFIX/share/omega-zsh" "$PREFIX/share/omega_zsh" "$PREFIX/etc/omega-zsh" "$PREFIX/etc/omega_zsh")
fi

confirm() {
  local prompt="${1:-Continue?}"
  [[ "$ASSUME_YES" == true ]] && return 0
  printf "%b" "${C_WARN}[?]${C_RESET} $prompt [y/N]: "
  read -r answer
  case "${answer,,}" in y|yes|s|si|sí) return 0 ;; *) return 1 ;; esac
}

safe_name() { printf "%s" "$1" | sed 's#/#__#g'; }

backup_file() {
  local file="$1"
  [[ "$DO_BACKUP" == true && -f "$file" ]] || return 0
  local dest="$RECOVERY_DIR/$(safe_name "$file")"

  if [[ "$DRY_RUN" == true ]]; then
    dry "Save single recovery copy: $file -> $dest"
    return 0
  fi

  mkdir -p "$RECOVERY_DIR"
  cp -p "$file" "$dest"
  ok "Recovery copy updated: $dest"
}

remove_path() {
  local target="$1"
  [[ -e "$target" || -L "$target" ]] || return 0
  log "Removing: $target"
  if [[ "$DRY_RUN" == true ]]; then dry "rm -rf -- $target"; else rm -rf -- "$target" && ok "Removed: $target"; fi
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

  local tmp; tmp="$(mktemp)"
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
  command -v python >/dev/null 2>&1 && { printf 'python'; return 0; }
  command -v python3 >/dev/null 2>&1 && { printf 'python3'; return 0; }
  return 1
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
    if [[ "$DRY_RUN" == true ]]; then dry "$py -m pip uninstall -y $pkg"; else "$py" -m pip uninstall -y "$pkg" || warn "Could not uninstall pip package: $pkg"; fi
  done <<< "$packages"
}

write_file() {
  local target="$1" content="$2"
  if [[ "$DRY_RUN" == true ]]; then dry "Write minimal safe config to $target"; else printf "%s\n" "$content" > "$target" && ok "Rebuilt: $target"; fi
}

path_block() {
  cat <<'EOF'
# Safe PATH
if [ -n "${PREFIX:-}" ]; then
  export PATH="$PREFIX/bin:$PATH"
fi
if [ -d "$HOME/.local/bin" ]; then
  export PATH="$HOME/.local/bin:$PATH"
fi
EOF
}

minimal_zshrc() {
  cat <<EOF
# ~/.zshrc rebuilt by Omega ZSH nuclear fix
# Previous version is stored once in ~/.omega-zsh-recovery when backups are enabled.

$(path_block)

export HISTFILE="\$HOME/.zsh_history"
export HISTSIZE=5000
export SAVEHIST=5000
setopt autocd extendedglob notify hist_ignore_dups share_history 2>/dev/null || true
autoload -Uz compinit 2>/dev/null && compinit 2>/dev/null || true

alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'

PROMPT='%F{cyan}%n@%m%f:%F{blue}%~%f %# '
EOF
}

minimal_bashrc() {
  cat <<EOF
# ~/.bashrc rebuilt by Omega ZSH nuclear fix
# Previous version is stored once in ~/.omega-zsh-recovery when backups are enabled.

$(path_block)

export HISTSIZE=5000
export HISTFILESIZE=5000
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
PS1='\u@\h:\w\$ '
EOF
}

minimal_profile() {
  cat <<EOF
# ~/.profile rebuilt by Omega ZSH nuclear fix
# Previous version is stored once in ~/.omega-zsh-recovery when backups are enabled.

$(path_block)
EOF
}

nuclear_fix_shell() {
  [[ "$NUCLEAR_FIX" == true ]] || return 0
  warn "Nuclear fix enabled: shell startup files will be rebuilt with minimal safe defaults."
  warn "Only one rotating recovery folder is used: $RECOVERY_DIR"
  confirm "Apply nuclear shell fix?" || { warn "Skipped nuclear shell fix."; return 0; }

  for file in "${CONFIG_FILES[@]}"; do [[ -f "$file" ]] && backup_file "$file"; done
  write_file "$HOME/.zshrc" "$(minimal_zshrc)"
  write_file "$HOME/.bashrc" "$(minimal_bashrc)"
  write_file "$HOME/.profile" "$(minimal_profile)"

  if [[ -f "$HOME/.bash_profile" ]]; then
    backup_file "$HOME/.bash_profile"
    if [[ "$DRY_RUN" == true ]]; then dry "Remove $HOME/.bash_profile to allow .profile fallback"; else rm -f "$HOME/.bash_profile" && ok "Removed: $HOME/.bash_profile"; fi
  fi
}

clean_extra_purge_paths() {
  [[ "$PURGE" == true ]] || return 0
  warn "Purge mode enabled: searching extra Omega-related paths."
  local roots=("$HOME/.config" "$HOME/.cache" "$HOME/.local/share" "$HOME/.local/bin") found=()
  [[ -n "${PREFIX:-}" ]] && roots+=("$PREFIX/bin" "$PREFIX/share" "$PREFIX/etc")

  for root in "${roots[@]}"; do
    [[ -d "$root" ]] || continue
    while IFS= read -r path; do found+=("$path"); done < <(find "$root" -maxdepth 2 \( -iname '*omega-zsh*' -o -iname '*omega_zsh*' -o -iname '*omegazsh*' \) 2>/dev/null)
  done

  [[ "${#found[@]}" -gt 0 ]] || { ok "No extra purge paths found."; return 0; }
  printf "\nExtra paths detected:\n"; printf "  - %s\n" "${found[@]}"; printf "\n"
  if confirm "Remove these extra paths?"; then for path in "${found[@]}"; do remove_path "$path"; done; else warn "Skipped extra purge cleanup."; fi
}

cat <<EOF

${C_INFO}OMEGA-ZSH UNINSTALLER / NUCLEAR FIX${C_RESET}

This script can remove Omega ZSH and repair broken shell startup files.

Safety model:
  - Default backup is a single rotating recovery folder: ~/.omega-zsh-recovery
  - Use --no-backup to disable recovery copies completely.
  - It will not remove zsh, oh-my-zsh, powerlevel10k, or external themes directly.

EOF

[[ "$DRY_RUN" == true ]] && warn "Dry-run mode enabled: no changes will be made."
[[ "$PURGE" == true ]] && warn "Purge mode enabled: extra Omega paths will be searched."
[[ "$NUCLEAR_FIX" == true ]] && warn "Nuclear fix enabled: shell startup files may be rebuilt."
[[ "$DO_BACKUP" == true ]] && log "Recovery folder: $RECOVERY_DIR" || warn "Recovery backups disabled."

confirm "Start Omega ZSH cleanup?" || { warn "Operation cancelled."; exit 0; }

log "Cleaning shell files..."; for file in "${CONFIG_FILES[@]}"; do clean_shell_file "$file"; done
log "Removing known launchers/binaries..."; for bin in "${CANDIDATE_BINS[@]}"; do remove_path "$bin"; done
log "Removing known Omega directories..."; for dir in "${CANDIDATE_DIRS[@]}"; do remove_path "$dir"; done
log "Checking related pip packages..."; uninstall_pip_packages
clean_extra_purge_paths
nuclear_fix_shell

ok "Cleanup finished."
[[ "$DRY_RUN" != true && "$DO_BACKUP" == true && -d "$RECOVERY_DIR" ]] && log "Recovery files are in: $RECOVERY_DIR"

cat <<'EOF'

Recommended next step:
  Restart your terminal or run:

    exec $SHELL -l

Nuclear fix usage:

    bash scripts/uninstall.sh --nuclear-fix
    bash scripts/uninstall.sh --dry-run --nuclear-fix
    bash scripts/uninstall.sh --no-backup --nuclear-fix

EOF
