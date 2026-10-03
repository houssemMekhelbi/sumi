# ~/.config/zsh/sumi-kami.zsh-theme
# Sumi kami prompt: standalone (no oh-my-zsh), no powerline blocks.
# Two lines, like a page: the context line, then the brush tip.
#   status  vermilion "✕ code", ⚡ root, ⚙ jobs; only when there is something to say
#   context muted user@host, only over SSH or as another user
#   dir     ink, bold (the shortened path)
#   git     indigo branch, vermilion ± when dirty
#   prompt  a vermilion › on the second line; the clock sits right, in tan
# Hex colours need zsh 5.7+ and a true-colour terminal.

setopt prompt_subst

SUMI_DEFAULT_USER=${SUMI_DEFAULT_USER:-rahal}   # hide context on your own box

S_TEXT='#16140F'  S_STRUCT='#3A3733' S_MUTED='#66615A'
S_TAN='#A39B8C'    S_SHU='#B3371F'     S_AI='#2E4A6B'

# ~/dotfiles/hypr -> ~/d/hypr
sumi_short_pwd() {
  local p=${(%):-%~}
  local -a parts=("${(@s:/:)p}")
  local i
  for (( i = 1; i < ${#parts}; i++ )); do
    [[ -z ${parts[i]} || ${parts[i]} == '~' ]] && continue
    if [[ ${parts[i]} == .* ]]; then
      parts[i]=${parts[i][1,2]}
    else
      parts[i]=${parts[i][1]}
    fi
  done
  print -rn -- "${(j:/:)parts//\%/%%}"
}

sumi_status() {
  local -a s
  (( SUMI_RETVAL != 0 )) && s+="✕ $SUMI_RETVAL"
  (( UID == 0 )) && s+="⚡"
  [[ -n ${jobstates} ]] && s+="⚙"
  (( ${#s} )) && print -n "%F{$S_SHU}${(j: :)s}%f  "
}

sumi_context() {
  [[ $USER != $SUMI_DEFAULT_USER || -n $SSH_CONNECTION ]] &&
    print -n "%F{$S_MUTED}%n@%m%f  "
}

sumi_dir() {
  print -n "%B%F{$S_STRUCT}$(sumi_short_pwd)%f%b"
}

sumi_git() {
  command git rev-parse --is-inside-work-tree &>/dev/null || return
  local ref
  ref=$(command git symbolic-ref --short HEAD 2>/dev/null) ||
    ref="➦ $(command git rev-parse --short HEAD 2>/dev/null)"
  ref=${ref//\%/%%}
  print -n "  %F{$S_AI}$ref%f"
  [[ -n $(command git status --porcelain --ignore-submodules=dirty 2>/dev/null | head -n1) ]] &&
    print -n "%F{$S_SHU} ±%f"
}

sumi_build_prompt() {
  sumi_status
  sumi_context
  sumi_dir
  sumi_git
}

sumi_precmd() { SUMI_RETVAL=$? }
autoload -Uz add-zsh-hook
add-zsh-hook precmd sumi_precmd

PROMPT='%{%f%b%k%}$(sumi_build_prompt)
%F{$S_SHU}›%f '
RPROMPT="%F{$S_TAN}%*%f"

# ---- completion ------------------------------------------------------
autoload -Uz compinit && compinit
zstyle ':completion:*' menu select
zstyle ':completion:*' list-colors 'ma=48;2;228;224;216;38;2;22;20;15'

# ---- plugins ---------------------------------------------------------
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE="fg=$S_TAN"
[[ -r /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh ]] &&
  source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh

# zsh-syntax-highlighting must be sourced last, then styled.
if [[ -r /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]]; then
  source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
  ZSH_HIGHLIGHT_STYLES[command]='fg=#16140F'
  ZSH_HIGHLIGHT_STYLES[builtin]='fg=#16140F'
  ZSH_HIGHLIGHT_STYLES[alias]='fg=#16140F'
  ZSH_HIGHLIGHT_STYLES[function]='fg=#16140F'
  ZSH_HIGHLIGHT_STYLES[precommand]='fg=#16140F,underline'
  ZSH_HIGHLIGHT_STYLES[path]='fg=#3A3733,underline'
  ZSH_HIGHLIGHT_STYLES[single-hyphen-option]='fg=#2E4A6B'
  ZSH_HIGHLIGHT_STYLES[double-hyphen-option]='fg=#2E4A6B'
  ZSH_HIGHLIGHT_STYLES[single-quoted-argument]='fg=#4F6B3A'
  ZSH_HIGHLIGHT_STYLES[double-quoted-argument]='fg=#4F6B3A'
  ZSH_HIGHLIGHT_STYLES[unknown-token]='fg=#B3371F,underline'
fi

export FZF_DEFAULT_OPTS="--color=bg+:#E4E0D8,fg:#66615A,fg+:#16140F,hl:#3A3733,hl+:#B3371F,pointer:#B3371F,prompt:#B3371F,info:#66615A,border:#D6CFC2 --pointer='▎' --prompt='› ' --border=rounded"
