# Clásico Elegante God Tier - "Royal Gold"
local return_code="%(?..%F{196}⛔ %?%f)"

# Paleta Luxury
local c_gold="%F{220}"
local c_slate="%F{238}"
local c_white="%F{255}"

local user_host="${c_gold}%n${c_slate}@${c_gold}%m"
local user_symbol='%(!.#.⚜)'
local current_dir="%B${c_white}%~%f"
local conda_prompt='$(conda_prompt_info)'
local vcs_branch='$(git_prompt_info)$(hg_prompt_info)'
local rvm_ruby='$(ruby_prompt_info)'
local venv_prompt='$(virtualenv_prompt_info)'

# Estilo Art Deco (Mixed Double/Single)
PROMPT="
${c_slate}╒═${c_gold}◈${c_slate}═ ${user_host} ${c_slate}═ ${current_dir}
${c_slate}╘═►%f ${user_symbol} "

RPROMPT="${c_slate}${conda_prompt}${vcs_branch}${venv_prompt} ${return_code}"

ZSH_THEME_GIT_PROMPT_PREFIX="${c_gold}git:❲"
ZSH_THEME_GIT_PROMPT_SUFFIX="${c_gold}❳%f"
ZSH_THEME_GIT_PROMPT_DIRTY="${c_white}●"
ZSH_THEME_GIT_PROMPT_CLEAN=""

ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX="${c_gold}venv:❲"
ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX="${c_gold}❳%f"
ZSH_THEME_VIRTUALENV_PREFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX"
ZSH_THEME_VIRTUALENV_SUFFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX"
