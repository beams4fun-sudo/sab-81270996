-- ServerBrowser.lua
-- Server Script inside ServerScriptService

local MemoryStoreService = game:GetService("MemoryStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TeleportService = game:GetService("TeleportService")

local serverMap = MemoryStoreService:GetSortedMap("ActiveServers")

-- Setup Remotes
local GetServerList = Instance.new("RemoteFunction", ReplicatedStorage)
GetServerList.Name = "GetServerList"

local JoinServer = Instance.new("RemoteFunction", ReplicatedStorage)
JoinServer.Name = "JoinServer"

local serverId = game.JobId
if serverId == "" then serverId = "LocalStudioServer" end

local function updateRegistry()
    local success, err = pcall(function()
        serverMap:SetAsync(serverId, {
            Name = "Server Instance " .. string.sub(serverId, 1, 6),
            Players = #game.Players:GetPlayers(),
            Rate = "$650M/s", -- Game specific currency rate
            AccessCode = serverId
        }, 600) -- Expire in 10 minutes
    end)
    if not success then
        warn("Failed to register server in MemoryStore: " .. tostring(err))
    end
end

-- Refresh registry loop
task.spawn(function()
    while true do
        updateRegistry()
        task.wait(300) -- Refresh every 5 minutes
    end
end)

-- Fetch List for Clients
GetServerList.OnServerInvoke = function(player)
    local success, result = pcall(function()
        return serverMap:GetRangeAsync(Enum.SortDirection.Ascending, 20)
    end)
    
    local list = {}
    if success and result then
        for _, entry in ipairs(result) do
            table.insert(list, entry.value)
        end
    end
    return list
end

-- Teleport request
JoinServer.OnServerInvoke = function(player, targetAccessCode)
    if targetAccessCode == serverId then return false end
    
    local success, err = pcall(function()
        -- Direct Teleport request
        TeleportService:TeleportToPlaceInstance(game.PlaceId, targetAccessCode, player)
    end)
    
    return success
end

-- Clean up on shut down
game:BindToClose(function()
    pcall(function()
        serverMap:RemoveAsync(serverId)
    end)
end)
