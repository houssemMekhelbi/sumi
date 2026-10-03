-- Hyprland 0.56.2
-- `hl` is provided globally.
-- This file is intentionally kept to display/session setup.
-- Desktop behavior, options, and keybinds live in futuwwa.lua.
-- Monitor rules live in monitors.lua, which belongs to no theme, so a theme
-- switch keeps them. A missing file (fresh install) falls back to Hyprland's
-- defaults; any other error in it is raised.
do
    local ok, err = pcall(require, "monitors")
    if not ok and not tostring(err):find("module 'monitors' not found", 1, true) then
        error(err)
    end
end

-- Session startup.
-- Waybar is managed by the user systemd waybar.service, so do not exec it here.
hl.on("hyprland.start", function()
    hl.exec_cmd("swaync")
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("hyprpolkitagent")
end)

-- Futuwwa behavior.
require("futuwwa")

-- Sumi kami look: ink on paper, brush strokes, one seal red.
require("sumi-kami")
