
-- Futuwwa desktop behavior.
-- Monitor geometry remains in hyprland.lua.

hl.config({
    input = {
        kb_layout = "fr",
        follow_mouse = 1,
    },


    general = {
        layout = "master",
        gaps_in = 4,
        gaps_out = 8,
        border_size = 2,
    },

    master = {
        mfact = 0.65,
        new_status = "master",
    },

    decoration = {
        rounding = 4,
        blur = {
            enabled = false,
        },
        shadow = {
            enabled = false,
        },
    },

    animations = {
        enabled = true,
    },
})

-----------------------------------------------------------------------
-- Core programs
-----------------------------------------------------------------------

-- foot runs as a server (foot-server.socket); each window is a footclient.
hl.bind("SUPER + RETURN",
    hl.dsp.exec_cmd("footclient"),
    { description = "Terminal" })

hl.bind("SUPER + CTRL + RETURN",
    hl.dsp.exec_cmd("footclient --app-id=foot-float"),
    { description = "Floating terminal" })

hl.bind("SUPER + SHIFT + RETURN",
    hl.dsp.exec_cmd("ghostty"),
    { description = "Ghostty" })

hl.bind("SUPER + ALT + RETURN",
    hl.dsp.exec_cmd("alacritty"),
    { description = "Alacritty" })

-- foot draws its own translucent background, so keep the window opaque.
hl.window_rule({
    name    = "foot-float",
    match   = { class = "^foot-float$" },
    float   = true,
    size    = "1000 600",
    center  = true,
    opacity = "1.0 override 1.0 override",
})

hl.bind("SUPER + D",
    hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/girih-launcher"),
    { description = "Application launcher" })

hl.bind("SUPER + Q",
    hl.dsp.window.close(),
    { description = "Close window" })

hl.bind("SUPER + F",
    hl.dsp.window.fullscreen({ mode = "fullscreen" }),
    { description = "Fullscreen" })

hl.bind("SUPER + SHIFT + SPACE",
    hl.dsp.window.float(),
    { description = "Toggle floating" })

hl.bind("SUPER + ALT + L",
    hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/hattin-lock"),
    { description = "Lock and wipe clipboard" })

-- Hyprland recommends hyprshutdown instead of the exit dispatcher.
hl.bind("SUPER + SHIFT + M",
    hl.dsp.exec_cmd("hyprshutdown"),
    { description = "Session menu" })

hl.bind("SUPER + B",
    hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/hattin-bluetooth-ui"),
    { description = "Bluetooth manager" })

hl.bind("SUPER + SHIFT + R",
    hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/hattin-monitor-recover"),
    { description = "Recover workspaces from disconnected monitors" })

-----------------------------------------------------------------------
-- Laptop / media keys
-----------------------------------------------------------------------

local fn_keys = {
    XF86AudioRaiseVolume = "volume-up",
    XF86AudioLowerVolume = "volume-down",
    XF86AudioMute = "volume-mute",
    XF86AudioMicMute = "mic-mute",
    XF86MonBrightnessUp = "brightness-up",
    XF86MonBrightnessDown = "brightness-down",
    XF86KbdBrightnessUp = "kbd-brightness-up",
    XF86KbdBrightnessDown = "kbd-brightness-down",
    XF86AudioPlay = "play-pause",
    XF86AudioNext = "next",
    XF86AudioPrev = "previous",
}

for key, action in pairs(fn_keys) do
    hl.bind(key,
        hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/hattin-keys " .. action),
        { description = "Hardware key: " .. action })
end

-----------------------------------------------------------------------
-- Vim + arrow focus
-----------------------------------------------------------------------

local focus = {
    H = "l",
    J = "d",
    K = "u",
    L = "r",
    LEFT  = "l",
    DOWN  = "d",
    UP    = "u",
    RIGHT = "r",
}

for key, direction in pairs(focus) do
    hl.bind(
        "SUPER + " .. key,
        hl.dsp.focus({ direction = direction }),
        { description = "Focus " .. direction }
    )
end

-----------------------------------------------------------------------
-- Move windows with Super+Shift+Vim / arrows
-----------------------------------------------------------------------

for key, direction in pairs(focus) do
    hl.bind(
        "SUPER + SHIFT + " .. key,
        hl.dsp.window.move({ direction = direction }),
        { description = "Move window " .. direction }
    )
end

-----------------------------------------------------------------------
-- Workspaces: per-monitor blocks, number-row binds, hotplug restore.
-----------------------------------------------------------------------

require("workspaces")

-----------------------------------------------------------------------
-- Master layout controls
-----------------------------------------------------------------------

hl.bind(
    "SUPER + COMMA",
    hl.dsp.layout("mfact -0.05"),
    { description = "Shrink master" }
)

hl.bind(
    "SUPER + PERIOD",
    hl.dsp.layout("mfact +0.05"),
    { description = "Grow master" }
)

hl.bind(
    "SUPER + M",
    hl.dsp.layout("swapwithmaster master"),
    { description = "Promote to master" }
)

-- Toggle master / dwindle.
hl.bind("SUPER + SPACE", function()
    local layout = hl.get_config("general.layout")

    if layout == "master" then
        hl.config({ general = { layout = "dwindle" } })
    else
        hl.config({ general = { layout = "master" } })
    end
end, { description = "Toggle master/dwindle layout" })

-----------------------------------------------------------------------
-- Hotplug behavior
--
-- Hyprland migrates workspaces/windows away from a disappearing output.
-- We additionally force keyboard focus onto the laptop/centre display.
--
-- Reconnecting a monitor moves its own workspaces back to it; see the
-- monitor.added handler in workspaces.lua.
-----------------------------------------------------------------------

hl.on("monitor.removed", function(_monitor)
    hl.exec_cmd("sh -c 'sleep 1; $HOME/.local/bin/hattin-monitor-recover eDP-1'")
    hl.dispatch(hl.dsp.focus({ monitor = "eDP-1" }))
end)

-----------------------------------------------------------------------
-- Useful scratchpad
-----------------------------------------------------------------------

hl.bind(
    "SUPER + S",
    hl.dsp.workspace.toggle_special("scratch"),
    { description = "Toggle scratchpad" }
)

hl.bind(
    "SUPER + SHIFT + S",
    hl.dsp.window.move({
        workspace = "special:scratch",
        follow = false,
    }),
    { description = "Send window to scratchpad" }
)
