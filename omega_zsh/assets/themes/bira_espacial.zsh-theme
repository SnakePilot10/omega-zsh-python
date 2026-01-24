# Espacial Galáctico God Tier - "USS Enterprise"
local return_code="%(?..%F{196}💥 HULL BREACH %?%f)"

# Paleta Estelar
local c_void="%F{019}"
local c_star="%F{231}"
local c_nebula="%F{051}"
local c_ship="%F{033}"

local user_host="${c_ship}🚀 COMMANDER@%m"
local user_symbol='%(!.#.🛸)'
local current_dir="%B${c_nebula}%~%f"
local conda_prompt='$(conda_prompt_info)'
local vcs_branch='$(git_prompt_info)$(hg_prompt_info)'
local rvm_ruby='$(ruby_prompt_info)'
local venv_prompt='$(virtualenv_prompt_info)'

# Diseño Orbital (Flight Path)
PROMPT="
${c_void}╭─${c_star}✧${c_void}┄┄${user_host} ${c_void}┄┄┄ ${current_dir}
${c_void}╰┄►%f ${user_symbol} "

RPROMPT="${c_void}system: [${conda_prompt}${vcs_branch}${venv_prompt}] ${return_code}"

ZSH_THEME_GIT_PROMPT_PREFIX="${c_ship}git:("
ZSH_THEME_GIT_PROMPT_SUFFIX="${c_ship})%f"
ZSH_THEME_GIT_PROMPT_DIRTY="${c_star}✶"
ZSH_THEME_GIT_PROMPT_CLEAN=""

ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX="${c_ship}env:("
ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX="${c_ship})%f"
ZSH_THEME_VIRTUALENV_PREFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX"
ZSH_THEME_VIRTUALENV_SUFFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX"




