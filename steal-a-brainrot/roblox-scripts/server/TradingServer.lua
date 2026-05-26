-- TradingServer.lua
-- Server Script inside ServerScriptService

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")

-- Setup Remotes
local RequestTrade = Instance.new("RemoteEvent", ReplicatedStorage)
RequestTrade.Name = "RequestTrade"

local AcceptTrade = Instance.new("RemoteEvent", ReplicatedStorage)
AcceptTrade.Name = "AcceptTrade"

local DeclineTrade = Instance.new("RemoteEvent", ReplicatedStorage)
DeclineTrade.Name = "DeclineTrade"

local ConfirmTrade = Instance.new("RemoteEvent", ReplicatedStorage)
ConfirmTrade.Name = "ConfirmTrade"

local TradeUpdate = Instance.new("RemoteEvent", ReplicatedStorage)
TradeUpdate.Name = "TradeUpdate"

-- Active Trades Table
local activeSessions = {}

RequestTrade.OnServerEvent:Connect(function(player, partnerName)
    local partner = game.Players:FindFirstChild(partnerName)
    if not partner or partner == player then return end
    
    -- Ensure neither player is already trading
    if activeSessions[player.UserId] or activeSessions[partner.UserId] then
        return
    end

    -- Create pending invitation session
    activeSessions[player.UserId] = {
        partnerId = partner.UserId,
        status = "Pending",
        time = os.time()
    }
    
    -- Notify partner
    TradeUpdate:FireClient(partner, "Request", player.Name)
end)

AcceptTrade.OnServerEvent:Connect(function(player, partnerName)
    local partner = game.Players:FindFirstChild(partnerName)
    if not partner then return end
    
    local session = activeSessions[partner.UserId]
    if session and session.partnerId == player.UserId and session.status == "Pending" then
        session.status = "Active"
        activeSessions[player.UserId] = {
            partnerId = partner.UserId,
            status = "Active",
            time = os.time()
        }
        
        -- Start Trade UI on both clients
        TradeUpdate:FireClient(player, "Start", partner.Name)
        TradeUpdate:FireClient(partner, "Start", player.Name)
    end
end)

DeclineTrade.OnServerEvent:Connect(function(player, partnerName)
    local partner = game.Players:FindFirstChild(partnerName)
    if partner then
        activeSessions[partner.UserId] = nil
        TradeUpdate:FireClient(partner, "Cancelled")
    end
    activeSessions[player.UserId] = nil
    TradeUpdate:FireClient(player, "Cancelled")
end)

ConfirmTrade.OnServerEvent:Connect(function(player)
    local session = activeSessions[player.UserId]
    if not session or session.status ~= "Active" then return end
    
    session.confirmed = true
    
    local partnerSession = activeSessions[session.partnerId]
    if partnerSession and partnerSession.confirmed then
        -- Atomically swap items here...
        local partner = game.Players:GetPlayerByUserId(session.partnerId)
        
        -- Update clients
        TradeUpdate:FireClient(player, "Success")
        TradeUpdate:FireClient(partner, "Success")
        
        -- Log webhook trigger
        local WebhookService = require(game.ServerScriptService:WaitForChild("WebhookService"))
        WebhookService.sendTradeCompleted(player.Name, partner.Name, "Brainrot Items")
        
        -- Cleanup
        activeSessions[player.UserId] = nil
        activeSessions[partner.UserId] = nil
    end
end)
