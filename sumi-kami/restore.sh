#!/usr/bin/env bash
# Switch the desktop to this theme: copy ./home over $HOME (after backing up
# whatever is there now), remove the previous theme's files that this theme
# does not have (previous = ~/.local/state/hattin-theme/current; its font
# files stay, running programs still read them) and the
# paths listed in ./ABSENT, point ~/.zshrc at this theme's prompt, re-apply
# gsettings, refresh font/icon caches, rebuild the mawaqit-api image if
# needed, (re)start the user services and record this theme as current.
# The theme name is this directory's name (girih, kyoka-delta, ...); the same
# script works in every theme directory.
#
#   ./restore.sh              restore everything
#   ./restore.sh --dry-run    show what would change, touch nothing
#   ./restore.sh --files-only copy files + gsettings, leave services alone
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
name=$(basename "$here")
cd "$here"

dry=0 services=1
for a in "$@"; do
    case $a in
        --dry-run) dry=1 ;;
        --files-only) services=0 ;;
        -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
        *) echo "unknown option: $a" >&2; exit 2 ;;
    esac
done

[[ -d home ]] || { echo "no ./home snapshot here" >&2; exit 1; }

say() { printf '\033[38;2;143;227;242m╱\033[0m %s\n' "$*"; }
run() { if ((dry)); then echo "  would run: $*"; else "$@"; fi; }
list() { [[ -f $1 ]] && grep -vE '^\s*(#|$)' "$1" || true; }

# --- packages: report only, installing needs sudo -------------------------
if command -v pacman >/dev/null; then
    mapfile -t want < <(grep -vE '^\s*#' packages.txt | tr ' ' '\n' | grep -v '^$')
    mapfile -t lack < <(pacman -T "${want[@]}" 2>/dev/null || true)
    if ((${#lack[@]})); then
        say "missing packages: ${lack[*]}"
        echo "  install with: sudo pacman -S --needed ${lack[*]}"
    fi
fi

# --- what the previous theme leaves behind ---------------------------------
# Files in the previous theme's snapshot that this theme does not ship.
marker="$HOME/.local/state/hattin-theme/current"
prev=$(cat "$marker" 2>/dev/null || true)
stale=()
# The previous theme sits next to this one (../<prev>) or, when the
# themes are cloned as separate repositories side by side, one level up
# (<repo>/<prev>).
prevdir=
if [[ -n $prev && $prev != "$name" ]]; then
    for d in "$here/../$prev" "$here"/../../*/"$prev"; do
        [[ -d $d/home ]] && { prevdir=$d; break; }
    done
fi
if [[ -n $prevdir ]]; then
    mapfile -t stale < <(comm -23 \
        <(cd "$prevdir/home" && find . -type f -o -type l | sed 's|^\./||' | sort) \
        <(cd home && find . -type f -o -type l | sed 's|^\./||' | sort))
fi

# --- backup ---------------------------------------------------------------
mapfile -t paths < <(list MANIFEST)
mapfile -t absent < <(list ABSENT)
existing=()
for p in "${paths[@]}" "${absent[@]}" "${stale[@]}" .zshrc; do [[ -e $HOME/$p || -L $HOME/$p ]] && existing+=("$p"); done

backup="$HOME/themes/.backups/before-$name-$(date +%Y%m%d-%H%M%S)"
if ((${#existing[@]})); then
    say "backing up ${#existing[@]} current paths -> $backup"
    if ((!dry)); then
        mkdir -p "$backup"
        bsdtar -C "$HOME" -cf - "${existing[@]}" | bsdtar -C "$backup" -xpf -
        # One switch backup per theme: the older ones go.
        for old in "${backup%-*-*}"-[0-9]*; do
            [[ -d $old && $old != "$backup" ]] && rm -rf "$old"
        done
    fi
else
    backup=
fi
((dry)) && backup=

# --- files ----------------------------------------------------------------
say "copying snapshot into $HOME"
if ((dry)); then
    (cd home && find . -type f | sed "s|^\./|  |" | head -40) || true
    echo "  ..."
else
    bsdtar -C home -cf - . | bsdtar -C "$HOME" -xpf -
fi

# Font files of the previous theme stay where they are. A running program keeps
# the font paths it resolved at start; once such a file is gone every glyph it
# has not drawn yet becomes an empty box until the program is restarted (seen
# with GTK apps left open across a switch). They cost a few MB per theme, no
# theme's fontconfig refers to another theme's families, and switching back to
# that theme overwrites them. To clear them by hand when nothing uses them:
#   rm -rf ~/.local/share/fonts/<other-theme> && fc-cache -f
n=0 kept=0
for p in "${stale[@]}"; do
    [[ -e $HOME/$p || -L $HOME/$p ]] || continue
    if [[ $p == .local/share/fonts/* ]]; then
        kept=$((kept + 1))
        continue
    fi
    run rm -f -- "${HOME:?}/$p"
    ((dry)) || (cd "$HOME" && rmdir -p --ignore-fail-on-non-empty "$(dirname "$p")" 2>/dev/null) || true
    n=$((n + 1))
done
((n)) && say "removed $n files of $prev that $name does not use (kept in the backup)"
((kept)) && say "left $kept font files of $prev in place (running programs still read them)"

for p in "${absent[@]}"; do
    if [[ -e $HOME/$p ]]; then
        say "removing $p (not part of $name; kept in the backup)"
        run rm -rf -- "${HOME:?}/$p"
    fi
done

# ~/.zshrc sources exactly one theme prompt: replace any other theme's line.
zshrc="$HOME/.zshrc"
theme_file=".config/zsh/$name.zsh-theme"
line="[ -r \"\$HOME/$theme_file\" ] && source \"\$HOME/$theme_file\""
if [[ -f home/$theme_file ]] && ! grep -qxF "$line" "$zshrc" 2>/dev/null; then
    say "pointing ~/.zshrc at the $name prompt"
    if ((!dry)); then
        touch "$zshrc"
        python3 - "$zshrc" "$line" "$name" <<'EOF'
import re, sys
path, line, name = sys.argv[1:]
text = open(path, encoding="utf-8").read().splitlines()
src = re.compile(r'^\[ -r "\$HOME/\.config/zsh/[\w-]+\.zsh-theme" \] && source ')
note = re.compile(r"^# \w+ prompt, completion colours and plugins\.$")
out, done = [], False
for l in text:
    if src.match(l):
        if not done:
            out.append(line)
            done = True
        continue
    if note.match(l):
        l = f"# {name.capitalize()} prompt, completion colours and plugins."
    out.append(l)
if not done:
    out += ["", f"# {name.capitalize()} prompt, completion colours and plugins.", line]
open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
EOF
    fi
fi

# --- gsettings, caches ----------------------------------------------------
say "applying gsettings"
icons= cursor= csize=
while IFS='=' read -r k v; do
    [[ -z $k || $k == \#* ]] && continue
    v=${v//\'/}
    case $k in
        icon-theme) icons=$v ;;
        cursor-theme) cursor=$v ;;
        cursor-size) csize=$v ;;
    esac
    run gsettings set org.gnome.desktop.interface "$k" "$v"
done < gsettings.txt
# A theme without a cursor gets the stock one back.
if [[ -z $cursor ]]; then
    cursor=default
    run gsettings set org.gnome.desktop.interface cursor-theme "$cursor"
fi
if [[ -z $csize ]]; then
    csize=24
    run gsettings set org.gnome.desktop.interface cursor-size "$csize"
fi

say "refreshing font and icon caches"
run fc-cache -f "$HOME/.local/share/fonts"
if [[ -n $icons && -d $HOME/.local/share/icons/$icons ]] && command -v gtk-update-icon-cache >/dev/null; then
    run gtk-update-icon-cache -f -t "$HOME/.local/share/icons/$icons" || true
fi

# --- services -------------------------------------------------------------
if ((services)); then
    say "reloading user services"
    run systemctl --user daemon-reload

    if command -v podman >/dev/null && ! podman image exists localhost/mawaqit-api; then
        say "building mawaqit-api image (upstream pins an EOL alpine, so override the base)"
        run podman build --from docker.io/library/python:3.12-alpine \
            -t localhost/mawaqit-api "$HOME/.local/share/mawaqit-api"
    fi
    run systemctl --user restart mawaqit-api.service || true

    run systemctl --user enable hattin-workspaces.service mawaqit-alerts.service
    run systemctl --user restart hattin-workspaces.service mawaqit-alerts.service || true
    run systemctl --user restart cliphist.service || true
    run systemctl --user restart waybar.service || true

    if [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]]; then
        run hyprctl reload >/dev/null || true
        # hyprpaper only reads its config at start; relaunch it under Hyprland.
        run pkill -x hyprpaper || true
        run hyprctl eval 'hl.exec_cmd("hyprpaper")' >/dev/null || true
        # swaync keeps the font files it started with, and a switch replaces them
        # (each theme vendors its fonts under its own name), so a CSS reload
        # (swaync-client -rs) leaves text as boxes: restart it instead. This
        # clears the notification history.
        if command -v swaync >/dev/null; then
            run pkill -x swaync || true
            ((dry)) || sleep 0.5
            run hyprctl eval 'hl.exec_cmd("swaync")' >/dev/null || true
        fi
        # The reload resets the cursor; set this theme's once it has settled.
        ((dry)) || sleep 1
        run hyprctl setcursor "$cursor" "$csize" >/dev/null || true
    fi
    # GTK3 reads gtk.css once per process: quit the Thunar daemon (and its
    # windows) so the next window starts with this theme's stylesheet.
    if pgrep -x Thunar >/dev/null; then
        run thunar -q || true
    fi
    # A running tmux server keeps its old status line until it re-reads the config.
    if command -v tmux >/dev/null && tmux list-sessions >/dev/null 2>&1; then
        run tmux source-file "$HOME/.config/tmux/tmux.conf" || true
    fi
fi

if ((!dry)); then
    mkdir -p "$(dirname "$marker")"
    printf '%s\n' "$name" > "$marker"
fi

say "done${backup:+ — previous files kept in $backup}"
((dry)) && echo "(dry run: nothing was changed)"
echo "Open terminals keep the old prompt until you start a new shell (or: exec zsh)."
