<p align="center"><img src=".github/banner.png" alt="Sumi: ink on paper, in two variants" width="100%"></p>

<p align="center"><sub>一筆入魂 ippitsu nyūkon: one stroke, the whole soul<br>
墨に五彩あり sumi ni gosai ari: ink holds five colours</sub></p>

# 墨 Sumi

Ink on paper: five ink tones and one seal red. Vermilion appears only where a seal would sit: the focus mark, an urgent window, a task due today, the banner, the lock.

| | |
|---|---|
| **sumi-kami** 紙 | paper: ink on washi, a light theme |
| **sumi-yoru** 夜 | night: silver ink on sumi black |

## 一 The inks

| | | |
|---|---|---|
| **ground** | `#EEE8DC / #15130F` | paper / sumi |
| **text** | `#16140F / #E9E2D4` | the ink |
| **seal** | `#C8412B / #D2492F` | the one red |
| **indigo** | `#2E4A6B / #7FA1C6` | data |

## 二 The strokes

- **Windows**: gaps 6/14, a 1px ink border, rounding 3, near-opaque paper, a soft
  ink shadow
- **Waybar**: three pale ink strokes with dry, ragged ends; ink-drop workspaces ○ ● ◌
- **mawaqit**: a paper card with a vermilion seal (時 adhan, 立 iqama), the prayer in
  Newsreader italic, the Arabic in Amiri
- **yawm**: `YAWM n` in vermilion when due, a pressed seal when overdue
- **hyprlock**: a Yuji Syuku clock, the password on a brush stroke, the saying in
  vertical columns with a seal; no username
- **SumiKamiFude / SumiYoruFude** brush cursors, **SumiKami / SumiYoru** icons,
  **GTK / Thunar** (a brush stroke under the current crumb and the selected file),
  **swaync**
- **Terminals**: DM Mono 10.5; tmux with a solid ink block; a two-line zsh prompt
- **Type**: Yuji Syuku, Newsreader, Instrument Sans, DM Mono

## 三 Grinding the ink

- Arch Linux (the package check uses `pacman`)
- Hyprland 0.56 or newer: the configuration is written in Lua
- waybar 0.15 or newer
- the packages in `sumi-kami/packages.txt` (both variants need the same):

```sh
sudo pacman -S --needed $(grep -v '^#' sumi-kami/packages.txt)
```

## 四 On paper

> [!WARNING]
> This is a whole desktop, not a colour scheme. It replaces every file listed
> in `sumi-kami/MANIFEST` or `sumi-yoru/MANIFEST`: the Hyprland, waybar, terminal, tmux, GTK and fontconfig
> configuration among them, and the theme line in `~/.zshrc`.
> Everything it replaces is backed up first.

```sh
git clone https://github.com/houssemMekhelbi/hattin-sumi.git
cd hattin-sumi
./sumi-kami/restore.sh --dry-run   # show what would change, touch nothing
./sumi-kami/restore.sh             # apply sumi-kami
./sumi-yoru/restore.sh             # or sumi-yoru
```

`restore.sh` then:

1. reports missing packages;
2. backs up every path it is about to replace to `~/themes/.backups/before-<variant>-<timestamp>/`;
3. copies the theme's `home/` over `$HOME` and removes the paths in its `ABSENT`;
4. points `~/.zshrc` at the theme's prompt;
5. applies its `gsettings.txt` and refreshes the font and icon caches;
6. builds the mawaqit-api image if it is missing, enables the user services and
   reloads Hyprland, waybar, hyprpaper, swaync and tmux.

`--files-only` copies the files and gsettings and leaves the services alone.

## 五 A clean sheet

Copy the backup folder back over `$HOME`.

## 六 Prayer times

Prayer times come from [mawaqit.net](https://mawaqit.net) through a local copy of
[mawaqit-api](https://github.com/mrsofiane/mawaqit-api), run by podman on 127.0.0.1.
List your mosques in `~/.config/mawaqit/mosques`, one `<mawaqit.net slug> | <label>`
per line; scroll or right-click the prayer module to switch between them.

## 七 Other papers

This is one of the hattin themes. They share one behaviour (binds, workspaces,
bar modules) and differ only in look. Clone several side by side and run the
`restore.sh` of the one you want: each switch removes what the previous theme
left that the new one does not use.

## 印 Licence

MIT, see [LICENSE](LICENSE). The fonts in `<theme>/home/.local/share/fonts/` are
under the SIL Open Font License; each licence text sits next to its font.
mawaqit-api (`<theme>/home/.local/share/mawaqit-api/`) is MIT, © Sofiane Louchene.
