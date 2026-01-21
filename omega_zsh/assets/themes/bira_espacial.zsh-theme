# Espacial Galáctico
local return_code="%(?..%{$fg[red]%}%? ERR%{$reset_color%})"
local user_host="%B%(!.%{$fg[red]%}.%{$fg[cyan]%})%n@%m%{$reset_color%} "
local user_symbol='%(!.#.🚀)'
local current_dir="%B%{$fg[blue]%}%~%{$reset_color%}"
local conda_prompt='$(conda_prompt_info)'
local vcs_branch='$(git_prompt_info)$(hg_prompt_info)'
local rvm_ruby='$(ruby_prompt_info)'
local venv_prompt='$(virtualenv_prompt_info)'
if [[ "${plugins[@]}" =~ 'kube-ps1' ]]; then
    local kube_prompt='$(kube_ps1)'
else
    local kube_prompt=''
fi

ZSH_THEME_RVM_PROMPT_OPTIONS="i v g"

PROMPT="🌌 ${conda_prompt}${user_host}${current_dir}${rvm_ruby}${vcs_branch}${venv_prompt}${kube_prompt}
└─ %B${user_symbol}%b "
RPROMPT="%B%{$fg[red]%}${return_code}%b%{$reset_color%}"

ZSH_THEME_GIT_PROMPT_PREFIX="%{$fg[cyan]%}⭐["
ZSH_THEME_GIT_PROMPT_SUFFIX="]%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_DIRTY="%{$fg[red]%}⚠"
ZSH_THEME_GIT_PROMPT_CLEAN="%{$fg[green]%}🛸"

ZSH_THEME_HG_PROMPT_PREFIX="$ZSH_THEME_GIT_PROMPT_PREFIX"
ZSH_THEME_HG_PROMPT_SUFFIX="$ZSH_THEME_GIT_PROMPT_SUFFIX"
ZSH_THEME_HG_PROMPT_DIRTY="$ZSH_THEME_GIT_PROMPT_DIRTY"
ZSH_THEME_HG_PROMPT_CLEAN="$ZSH_THEME_GIT_PROMPT_CLEAN"

ZSH_THEME_RUBY_PROMPT_PREFIX="%{$fg[blue]%}💎["
ZSH_THEME_RUBY_PROMPT_SUFFIX="]%{$reset_color%}"

ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX="%{$fg[cyan]%}🪐["
ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX="]%{$reset_color%}"
ZSH_THEME_VIRTUALENV_PREFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX"
ZSH_THEME_VIRTUALENV_SUFFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX"

