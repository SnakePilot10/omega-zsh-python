# Minimalista Moderno God Tier - "Zen Garden"
local return_code="%(?..%F{196}× %?%f)"

local c_dim="%F{244}"
local c_main="%F{255}"

local user_host="${c_dim}%n@%m"
local user_symbol='%(!.#.›)'
local current_dir="%B${c_main}%~%f"

# Sharp Edge - Sin curvas, sin extensiones largas
PROMPT="
${c_dim}┌ ${user_host} ${c_dim}· ${current_dir}
${c_dim}└ ${c_main}${user_symbol} "

RPROMPT="${c_dim}$(git_prompt_info)$(virtualenv_prompt_info) ${return_code}"

ZSH_THEME_GIT_PROMPT_PREFIX="${c_dim}"
ZSH_THEME_GIT_PROMPT_SUFFIX=""
ZSH_THEME_GIT_PROMPT_DIRTY="*"
ZSH_THEME_GIT_PROMPT_CLEAN=""

ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX="${c_dim}py:"
ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX=""
ZSH_THEME_VIRTUALENV_PREFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX"
ZSH_THEME_VIRTUALENV_SUFFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX"
