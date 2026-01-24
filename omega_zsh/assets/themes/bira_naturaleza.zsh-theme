# Naturaleza Bosque God Tier - "Elven Forest"
local return_code="%(?..%F{160}🥀 %?%f)"

local c_leaf="%F{034}"
local c_bud="%F{154}"
local c_wood="%F{094}"

local user_host="${c_leaf}%n${c_wood}@${c_leaf}%m"
local user_symbol='%(!.#.❧)'
local current_dir="%B${c_bud}%~%f"
local conda_prompt='$(conda_prompt_info)'
local vcs_branch='$(git_prompt_info)$(hg_prompt_info)'
local rvm_ruby='$(ruby_prompt_info)'
local venv_prompt='$(virtualenv_prompt_info)'

# Estilo Enredadera (Organic Curves)
PROMPT="
${c_wood}╭〰〰${c_leaf}🌿${c_wood}〰 ${user_host} ${c_wood}〰 ${current_dir}
${c_wood}╰〰${c_bud}⚘ %f "

RPROMPT="${c_wood}${conda_prompt}${vcs_branch}${venv_prompt} ${return_code}"

ZSH_THEME_GIT_PROMPT_PREFIX="${c_leaf}git:❨"
ZSH_THEME_GIT_PROMPT_SUFFIX="${c_leaf}❩%f"
ZSH_THEME_GIT_PROMPT_DIRTY="${c_bud}🍂"
ZSH_THEME_GIT_PROMPT_CLEAN=""

ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX="${c_leaf}venv:❨"
ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX="${c_leaf}❩%f"
ZSH_THEME_VIRTUALENV_PREFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX"
ZSH_THEME_VIRTUALENV_SUFFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX"
