# Futurista Neon God Tier - "Night City HUD"
local return_code="%(?..%F{196}☠ %?%f)"

# Neon Palette: Pink 198/201, Cyan 051/045, Purple 093
local c_pink="%F{201}"
local c_cyan="%F{051}"
local c_purp="%F{093}"
local c_warn="%F{196}"

local user_host="${c_pink}❲ %n ${c_purp}⚡ ${c_cyan}%m ${c_pink}❳%f"
local user_symbol='%(!.#.❯❯❯)'
local current_dir="${c_cyan}📂 %~%f"
local conda_prompt='$(conda_prompt_info)'
local vcs_branch='$(git_prompt_info)$(hg_prompt_info)'
local rvm_ruby='$(ruby_prompt_info)'
local venv_prompt='$(virtualenv_prompt_info)'

# HUD Superior con Bloques Sólidos (Mecha Anime Style)
PROMPT="
${c_cyan}▛▀▀${c_pink}▀${c_purp}▀${c_pink}▀${c_cyan}▀${user_host}▀▀${current_dir}
${c_cyan}▙▄▄►%f ${user_symbol} "

# Info flotante a la derecha
RPROMPT="${c_purp}${conda_prompt}${venv_prompt}${vcs_branch} ${return_code}"

# Git estilo Cyber
ZSH_THEME_GIT_PROMPT_PREFIX="${c_pink}git:❲"
ZSH_THEME_GIT_PROMPT_SUFFIX="${c_pink}❳%f"
ZSH_THEME_GIT_PROMPT_DIRTY="${c_warn}✖"
ZSH_THEME_GIT_PROMPT_CLEAN="${c_cyan}✔"

ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX="${c_purp}sys:❲"
ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX="${c_purp}❳%f"
ZSH_THEME_VIRTUALENV_PREFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX"
ZSH_THEME_VIRTUALENV_SUFFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX"
