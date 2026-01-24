# Oscuro Gótico God Tier - "Nosferatu"
local return_code="%(?..%K{088}%F{015} 💀 FATAL ERROR %? %f%k)"
# Colores: Rojo Sangre 088, Rojo Vivo 196, Gris Muerto 240
local c_blood="%F{088}"
local c_bone="%F{250}"
local c_grey="%F{238}"

local user_host="${c_blood}𝕹𝖔𝖘𝖋𝖊𝖗𝖆𝖙𝖚@%m"
local user_symbol='%(!.#.⸸)'
local current_dir="%B${c_bone}%~%f"
local conda_prompt='$(conda_prompt_info)'
local vcs_branch='$(git_prompt_info)$(hg_prompt_info)'
local rvm_ruby='$(ruby_prompt_info)'
local venv_prompt='$(virtualenv_prompt_info)'

# Diseño sepulcral (Hierro Forjado)
PROMPT="
${c_grey}┏━${c_blood}⚰️━${user_host} ${c_grey}━━ ${current_dir}
${c_grey}┗━${c_blood}🩸%f "

RPROMPT="${c_grey}${conda_prompt}${vcs_branch}${venv_prompt} ${return_code}"

ZSH_THEME_GIT_PROMPT_PREFIX="${c_grey}git:❬"
ZSH_THEME_GIT_PROMPT_SUFFIX="${c_grey}❭%f"
ZSH_THEME_GIT_PROMPT_DIRTY="${c_blood}✖"
ZSH_THEME_GIT_PROMPT_CLEAN="${c_grey}✔"

ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX="${c_grey}venv:❬"
ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX="${c_grey}❭%f"
ZSH_THEME_VIRTUALENV_PREFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX"
ZSH_THEME_VIRTUALENV_SUFFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX"
