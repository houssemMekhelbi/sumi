-- Per-monitor workspaces.
--
-- Each output owns a fixed block of ten workspace ids and workspace rules pin
-- them there, so a workspace never migrates to another monitor. SUPER+1..0
-- always addresses the focused output's own block.
--
--   HDMI-A-2 (left)    1..10
--   eDP-1    (centre) 11..20
--   DP-6     (right)  21..30
--   anything else     30 + monitor.id * 10 + slot (unpinned)
--
-- Exposed as the global `hattin_ws` so Waybar can call it through
-- `hyprctl eval`. ~/.local/bin/hattin-workspaces reads the same blocks back
-- from the workspace rules, so this table is the single source of truth.

local M = {}

M.size = 10
M.bases = {
    ["HDMI-A-2"] = 0,
    ["eDP-1"]    = 10,
    ["DP-6"]     = 20,
}

for name, base in pairs(M.bases) do
    for slot = 1, M.size do
        hl.workspace_rule({
            workspace = tostring(base + slot),
            monitor   = name,
            default   = slot == 1,
        })
    end
end

function M.base(monitor)
    if not monitor then
        return 0
    end
    return M.bases[monitor.name] or (30 + monitor.id * M.size)
end

function M.id(slot, monitor)
    return M.base(monitor or hl.get_active_monitor()) + slot
end

function M.focus(slot, monitor)
    hl.dispatch(hl.dsp.focus({ workspace = M.id(slot, monitor) }))
end

function M.send(slot)
    hl.dispatch(hl.dsp.window.move({ workspace = M.id(slot), follow = true }))
end

-- Waybar click: the cursor is on the bar that was clicked.
function M.click(slot)
    M.focus(slot, hl.get_monitor_at_cursor())
end

-- Waybar click on the "foreign" slot: cycle through workspaces sitting on
-- this monitor that belong to another (usually disconnected) monitor.
function M.cycle_foreign()
    local monitor = hl.get_monitor_at_cursor()
    if not monitor then
        return
    end
    local base = M.base(monitor)
    local ids = {}
    for _, ws in ipairs(hl.get_workspaces()) do
        if not ws.special and ws.monitor and ws.monitor.name == monitor.name
            and (ws.id <= base or ws.id > base + M.size) then
            table.insert(ids, ws.id)
        end
    end
    if #ids == 0 then
        return
    end
    table.sort(ids)
    local current = monitor.active_workspace and monitor.active_workspace.id
    local target = ids[1]
    for _, id in ipairs(ids) do
        if current and id > current then
            target = id
            break
        end
    end
    hl.dispatch(hl.dsp.focus({ workspace = target }))
end

-- First empty slot on the focused monitor (not the one already shown).
function M.first_empty()
    local monitor = hl.get_active_monitor()
    local base = M.base(monitor)
    local used = {}
    for _, ws in ipairs(hl.get_workspaces()) do
        if ws.windows > 0 or ws.visible then
            used[ws.id] = true
        end
    end
    for slot = 1, M.size do
        if not used[base + slot] then
            M.focus(slot, monitor)
            return
        end
    end
end

-- Move every workspace back to its owning monitor if that monitor is present.
function M.restore()
    local present = {}
    for _, monitor in ipairs(hl.get_monitors()) do
        present[monitor.name] = true
    end
    for _, ws in ipairs(hl.get_workspaces()) do
        if not ws.special and ws.monitor then
            for name, base in pairs(M.bases) do
                if present[name] and ws.id > base and ws.id <= base + M.size
                    and ws.monitor.name ~= name then
                    hl.dispatch(hl.dsp.workspace.move({ workspace = ws.id, monitor = name }))
                end
            end
        end
    end
end

-----------------------------------------------------------------------
-- Binds: physical number row (XKB codes 10..19), AZERTY-safe.
-----------------------------------------------------------------------

local number_codes = { 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 }

for slot, code in ipairs(number_codes) do
    hl.bind("SUPER + code:" .. code,
        function() M.focus(slot) end,
        { description = "Workspace " .. slot .. " on this monitor" })

    hl.bind("SUPER + SHIFT + code:" .. code,
        function() M.send(slot) end,
        { description = "Move window to workspace " .. slot .. " on this monitor" })
end

-----------------------------------------------------------------------
-- Move window to the adjacent monitor (physical left/right order).
-----------------------------------------------------------------------

function M.send_to_monitor(direction)
    local monitors = hl.get_monitors()
    if #monitors < 2 then
        return
    end
    table.sort(monitors, function(a, b) return a.x < b.x end)

    local current = hl.get_active_monitor()
    local index
    for i, monitor in ipairs(monitors) do
        if current and monitor.name == current.name then
            index = i
            break
        end
    end
    if not index then
        return
    end

    local delta = direction == "right" and 1 or -1
    local target = monitors[((index - 1 + delta) % #monitors) + 1]
    local workspace = target.active_workspace
    if not workspace then
        return
    end

    hl.dispatch(hl.dsp.window.move({ workspace = workspace.id, follow = true }))
end

for _, spec in ipairs({
    { key = "LEFT",  dir = "left" },
    { key = "RIGHT", dir = "right" },
    { key = "H",     dir = "left" },
    { key = "L",     dir = "right" },
}) do
    hl.bind("SUPER + CTRL + " .. spec.key,
        function() M.send_to_monitor(spec.dir) end,
        { description = "Move window to monitor on the " .. spec.dir })
end

hl.bind("SUPER + TAB",
    hl.dsp.focus({ workspace = "previous_per_monitor" }),
    { description = "Previous workspace on this monitor" })

hl.bind("SUPER + N",
    function() M.first_empty() end,
    { description = "First empty workspace on this monitor" })

-----------------------------------------------------------------------
-- Hotplug: when a monitor comes back, its workspaces go back to it.
-- (Removal is still handled by hattin-monitor-recover in futuwwa.lua.)
-----------------------------------------------------------------------

hl.on("monitor.added", function(_monitor)
    hl.exec_cmd("sh -c 'sleep 1; hyprctl eval \"hattin_ws.restore()\"'")
end)

hattin_ws = M
return M
