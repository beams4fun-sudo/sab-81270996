-- InventoryReporter.lua
-- Place in ServerScriptService
-- Scans a player's brainrot inventory on join and reports it to the Flask API.

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")

-- Config
local API_BASE = "http://localhost:5000" -- Change to your hosted production domain
local REPORT_ENDPOINT = API_BASE .. "/api/roblox/inventory/report"

-- Scans the player's inventory folder and returns a list of owned brainrot names
local function scanPlayerInventory(player)
    local ownedItems = {}

    -- Approach 1: Check player's backpack / inventory folder
    -- This depends on how your game stores brainrots.
    -- Common patterns: ReplicatedStorage items tagged with CollectionService,
    -- or a Folder under the player named "Inventory" or "Brainrots"

    -- Check for an Inventory folder under the player
    local invFolder = player:FindFirstChild("Inventory") or player:FindFirstChild("Brainrots")
    if invFolder then
        for _, item in ipairs(invFolder:GetChildren()) do
            table.insert(ownedItems, item.Name)
        end
    end

    -- Approach 2: Check DataStore for stored inventory
    local DataStoreService = game:GetService("DataStoreService")
    local success, storedData = pcall(function()
        local store = DataStoreService:GetDataStore("PlayerBrainrots")
        return store:GetAsync("Inventory_" .. player.UserId)
    end)

    if success and storedData and type(storedData) == "table" then
        for _, itemName in ipairs(storedData) do
            table.insert(ownedItems, itemName)
        end
    end

    return ownedItems
end

-- Reports inventory to the Flask backend
local function reportInventory(player)
    local ownedItems = scanPlayerInventory(player)

    local payload = {
        player_id = tostring(player.UserId),
        player_name = player.Name,
        owned_items = ownedItems
    }

    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = REPORT_ENDPOINT,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(payload)
        })
    end)

    if success and response.StatusCode == 200 then
        local data = HttpService:JSONDecode(response.Body)
        if data.success then
            print(("[InventoryReporter] %s: %d/%d brainrots (%.1f%%)"):format(
                player.Name,
                data.analysis.count_owned,
                data.analysis.total,
                data.analysis.completion_pct
            ))
        end
    else
        warn("[InventoryReporter] Failed to report inventory for " .. player.Name .. ": " .. tostring(response))
    end
end

-- Hook into player join
Players.PlayerAdded:Connect(function(player)
    -- Small delay to allow inventory to load
    task.wait(3)
    reportInventory(player)
end)

-- Also report for any players already in the server
for _, player in ipairs(Players:GetPlayers()) do
    task.spawn(function()
        task.wait(1)
        reportInventory(player)
    end)
end

print("[InventoryReporter] Module loaded. Monitoring player inventories.")
