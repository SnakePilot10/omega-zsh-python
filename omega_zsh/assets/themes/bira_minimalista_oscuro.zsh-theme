# Minimalista Oscuro God Tier - "OLED Void"
local return_code="%(?..%F{124} ERR %?%f)"

local c_dark="%F{237}"
local c_text="%F{245}"
local c_accent="%F{025}"

local user_host="${c_dark}%n@%m"
local user_symbol='%(!.#.›)'
local current_dir="%B${c_text}%~%f"

# Disconnected Style (╷ ╰)
PROMPT="
${c_dark}╷ ${user_host} ${c_dark}:: ${current_dir}
${c_dark}╰ ${c_accent}${user_symbol}%f "

RPROMPT="${c_dark}$(git_prompt_info)$(virtualenv_prompt_info) ${return_code}"

ZSH_THEME_GIT_PROMPT_PREFIX="${c_dark}g:"
ZSH_THEME_GIT_PROMPT_SUFFIX=""
ZSH_THEME_GIT_PROMPT_DIRTY="*"
ZSH_THEME_GIT_PROMPT_CLEAN=""

ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX="${c_dark}v:"
ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX=""
ZSH_THEME_VIRTUALENV_PREFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX"
ZSH_THEME_VIRTUALENV_SUFFIX="$ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX"
