# Retro Terminal God Tier - "Fallout Pip-Boy"
local return_code="%(?..%K{046}%F{016} ERR %? %f%k)"

# Verde Fósforo Puro
local c_phos="%F{046}"
local c_dim="%F{022}"

local user_host="${c_phos}USR:%n@%m"
local user_symbol='%(!.#.█)'
local current_dir="%B${c_phos}DIR:%~%f"
local conda_prompt='$(conda_prompt_info)'
local vcs_branch='$(git_prompt_info)$(hg_prompt_info)'
local rvm_ruby='$(ruby_prompt_info)'
local venv_prompt='$(virtualenv_prompt_info)'

# Estilo BIOS Post-Apocalíptico
PROMPT="
${c_phos}╔═[ ${user_host} ]═[ ${current_dir} ]
${c_phos}╚═► ${user_symbol} "

RPROMPT="${c_phos}[ SYS:${conda_prompt}${vcs_branch}${venv_prompt} ] ${return_code}"

ZSH_THEME_GIT_PROMPT_PREFIX="GIT:"
ZSH_THEME_GIT_PROMPT_SUFFIX=""
ZSH_THEME_GIT_PROMPT_DIRTY="!"
ZSH_THEME_GIT_PROMPT_CLEAN=""

ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX="ENV:"
ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX=""
ZSH_THEME_VIRTUALENV_PREFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX"
ZSH_THEME_VIRTUALENV_SUFFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX"
