# Matrix God Tier - "The Construct"
local return_code="%(?..%F{196}ERROR:%?%f)"
# Colores Matrix: 46 (Brillante), 40, 34, 28, 22 (Oscuro)
local user_host="%B%F{046}%n%F{040}@%F{034}%m%f"
local user_symbol='%(!.#.>_)'

# Path con efecto "Digital Decay"
local current_dir="%B%F{118}[ %F{154}%~ %F{118}]%f"

local conda_prompt='$(conda_prompt_info)'
local vcs_branch='$(git_prompt_info)$(hg_prompt_info)'
local rvm_ruby='$(ruby_prompt_info)'
local venv_prompt='$(virtualenv_prompt_info)'
if [[ "${plugins[@]}" =~ 'kube-ps1' ]]; then
    local kube_prompt='$(kube_ps1)'
else
    local kube_prompt=''
fi

# Decoración binaria aleatoria estática para velocidad
local bin_deco="%F{022}10110%F{028}01%F{034}10%F{040}01%f"

# Estructura "Circuit Board" (╓ ╙)
PROMPT="
%F{028}╓──${bin_deco}──$user_host $current_dir
%F{028}╙─▪%B%F{046}${user_symbol}%f "

# Info técnica a la derecha para limpiar la vista
RPROMPT="${conda_prompt}${vcs_branch}${venv_prompt} ${return_code}"

# Git estilo "Raw Data"
ZSH_THEME_GIT_PROMPT_PREFIX="%F{046}git::"
ZSH_THEME_GIT_PROMPT_SUFFIX=""
ZSH_THEME_GIT_PROMPT_DIRTY="%F{196}![UNSYNC]"
ZSH_THEME_GIT_PROMPT_CLEAN="%F{046}[SYNC]"

ZSH_THEME_RUBY_PROMPT_PREFIX="%F{046}rb::"
ZSH_THEME_RUBY_PROMPT_SUFFIX=""

ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX="%F{046}venv::"
ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX=""

