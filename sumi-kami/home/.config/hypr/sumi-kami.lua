-- Sumi kami look and feel.
-- Ink on paper: five ink tones, one seal red. Loaded after futuwwa.lua so
-- these values win; behaviour and binds stay there.
--
-- Windows are plain paper with a 1px ink border and almost no rounding; the
-- brush lives where we draw: the wallpaper, the bar strokes (waybar), the
-- prayer banner, the lock screen, icons and cursor. Vermilion is used only
-- where a seal would sit (focus marks, urgent, due); never for structure.

local C = {
    ground = "EEE8DC",
    ink    = "3A3733",
    quiet  = "CFC8BB",
    shadow = "16140F",
}

hl.config({
    general = {
        gaps_in     = 6,
        gaps_out    = 14,
        border_size = 1,
        col = {
            active_border   = "rgb(" .. C.ink .. ")",
            inactive_border = "rgb(" .. C.quiet .. ")",
        },
    },

    decoration = {
        rounding       = 3,
        rounding_power = 2.0,

        active_opacity   = 0.97,
        inactive_opacity = 0.93,

        blur = {
            enabled           = true,
            size              = 6,
            passes            = 2,
            vibrancy          = 0.0,
            noise             = 0.02,
            new_optimizations = true,
            popups            = true,
        },

        glow = {
            enabled = false,
        },

        -- A soft ink shadow under the paper, stronger on the focused sheet.
        shadow = {
            enabled        = true,
            range          = 24,
            render_power   = 3,
            offset         = { 0, 8 },
            color          = "rgba(" .. C.shadow .. "29)",
            color_inactive = "rgba(" .. C.shadow .. "14)",
        },
    },

    group = {
        col = {
            border_active   = "rgb(" .. C.ink .. ")",
            border_inactive = "rgb(" .. C.quiet .. ")",
        },
    },

    misc = {
        disable_hyprland_logo    = true,
        disable_splash_rendering = true,
        background_color         = "rgb(" .. C.ground .. ")",
    },
})

-- Cursor: SumiKamiFude (~/.local/share/icons/SumiKamiFude, hyprcursor + XCursor).
-- On a live theme switch restore.sh runs `hyprctl setcursor` from gsettings.txt.
hl.env("HYPRCURSOR_THEME", "SumiKamiFude")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("XCURSOR_THEME", "SumiKamiFude")
hl.env("XCURSOR_SIZE", "24")

-- A config reload resets the cursor to the default theme; set it again.
local function sumi_cursor()
    hl.exec_cmd("hyprctl setcursor SumiKamiFude 24")
end
hl.on("hyprland.start", sumi_cursor)
hl.on("config.reloaded", sumi_cursor)

-- Launcher bind points at the Sumi launcher; futuwwa.lua binds the Girih one.
hl.unbind("SUPER + D")
hl.bind("SUPER + D",
    hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/sumi-launcher"),
    { description = "Application launcher" })

-- Terminals draw their own paper (foot/alacritty/ghostty alpha) so text stays opaque.
hl.window_rule({
    name    = "sumi-terminal-opaque",
    match   = { class = "^(foot|footclient|Alacritty|com.mitchellh.ghostty)$" },
    opacity = "1.0 override 1.0 override",
})

-- Blur behind layer surfaces: waybar strokes, alert banners, launcher, notifications.
-- ignore_alpha keeps the paper between the bar strokes unblurred.
hl.layer_rule({
    name         = "sumi-bar-glass",
    match        = { namespace = "^hattin-" },
    blur         = true,
    ignore_alpha = 0.1,
})

hl.layer_rule({
    name         = "sumi-launcher-glass",
    match        = { namespace = "^launcher$" },
    blur         = true,
    ignore_alpha = 0.1,
})

hl.layer_rule({
    name         = "sumi-notify-glass",
    match        = { namespace = "^swaync" },
    blur         = true,
    ignore_alpha = 0.1,
})

-- Launcher: floating foot + fzf (~/.local/bin/sumi-launcher).
hl.window_rule({
    name     = "sumi-launcher",
    match    = { class = "^sumi-launcher$" },
    float    = true,
    size     = "780 470",
    center   = true,
    pin      = true,
    opacity  = "1.0 override 1.0 override",
})

-- Taskwarrior popups from the waybar "yawm" module (~/.local/bin/sumi-yawm).
hl.window_rule({
    name     = "sumi-yawm",
    match    = { class = "^sumi-yawm$" },
    float    = true,
    size     = "820 600",
    center   = true,
    pin      = true,
    opacity  = "1.0 override 1.0 override",
})

hl.window_rule({
    name     = "sumi-yawm-add",
    match    = { class = "^sumi-yawm-add$" },
    float    = true,
    size     = "720 240",
    center   = true,
    pin      = true,
    opacity  = "1.0 override 1.0 override",
})

local sumi_popups = { "sumi-launcher", "sumi-yawm", "sumi-yawm-add" }

-- Close every popup window except those of class `keep`.
-- hl.get_windows matches `class` exactly (no regex), so pass the plain name.
function sumi_close_popups(keep)
    for _, class in ipairs(sumi_popups) do
        if class ~= keep then
            for _, w in ipairs(hl.get_windows({ class = class })) do
                hl.dispatch(hl.dsp.window.close({ window = "address:" .. w.address }))
            end
        end
    end
end

function sumi_close_launcher()
    sumi_close_popups()
end

-- Close popups as soon as focus moves elsewhere.
hl.on("window.active", function(win)
    sumi_close_popups(win and win.class)
end)
