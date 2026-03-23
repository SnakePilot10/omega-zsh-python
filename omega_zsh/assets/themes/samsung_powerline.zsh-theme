function _git_seg() {
  local branch
  branch=$(git symbolic-ref --short HEAD 2>/dev/null)

  if [[ -n "$branch" ]]; then
    # Separador path→git (charcoal→rojo) + texto + trailing diamond
    echo -n "%F{#252525}%K{#e4002b}%F{#ffffff} ${branch} %k%F{#e4002b}%f"
  else
    # Sin repo: cierra el fondo del path con trailing diamond sutil
    echo -n "%k%F{#252525}%f"
  fi
}

PROMPT='%F{#1428A0}%K{#1428A0}%F{#ffffff} %n %F{#1428A0}%K{#252525}%F{#ffffff} %1~ $(_git_seg)
%F{#1428A0}╰─⮞%f '
