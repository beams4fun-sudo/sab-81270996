-- KeyValidationServer.lua
-- Place in ServerScriptService

local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local DataStoreService = game:GetService("DataStoreService")

local licenseStore = DataStoreService:GetDataStore("LicenseStore")

-- Config
local API_URL = "http://localhost:5000/api/validate" -- Change to your hosted production domain

-- Setup Remotes
local ValidateKey = Instance.new("RemoteFunction")
ValidateKey.Name = "ValidateKey"
ValidateKey.Parent = ReplicatedStorage

-- Attempts cache to prevent spamming HTTP requests
local validationAttempts = {}

ValidateKey.OnServerInvoke = function(player, keyString)
    -- Clean the key string
    keyString = string.gsub(keyString, "%s+", "")

    -- Basic Rate Limiting
    local now = os.time()
    local playerAttempts = validationAttempts[player.UserId] or {count = 0, lastTime = 0}
    
    if now - playerAttempts.lastTime < 60 then
        if playerAttempts.count >= 3 then
            return {valid = false, message = "Too many attempts. Please wait 1 minute."}
        end
        playerAttempts.count = playerAttempts.count + 1
    else
        playerAttempts.count = 1
        playerAttempts.lastTime = now
    end
    validationAttempts[player.UserId] = playerAttempts

    -- 1. Check local cache / DataStore first (optimization)
    local success, cachedKey = pcall(function()
        return licenseStore:GetAsync("User_" .. player.UserId)
    end)

    if success and cachedKey == keyString then
        return {valid = true, message = "Verified from local cache."}
    end

    -- 2. Call external validation API
    local apiPayload = {
        key = keyString,
        hwid = tostring(player.UserId), -- Binding to Roblox User ID as stable HWID in Roblox sandbox
        player_id = tostring(player.UserId),
        player_name = player.Name
    }

    local apiSuccess, apiResponse = pcall(function()
        return HttpService:RequestAsync({
            Url = API_URL,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(apiPayload)
        })
    end)

    if apiSuccess and apiResponse.StatusCode == 200 then
        local data = HttpService:JSONDecode(apiResponse.Body)
        if data.valid then
            -- Cache activation locally
            pcall(function()
                licenseStore:SetAsync("User_" .. player.UserId, keyString)
            end)
            return {valid = true, message = "License validated."}
        else
            return {valid = false, message = data.message or "Invalid license key."}
        end
    else
        warn("Validation server unreachable: " .. tostring(apiResponse))
        return {valid = false, message = "System validation server is currently offline."}
    end
end

-- Clear validation logs on exit
game.Players.PlayerRemoving:Connect(function(player)
    validationAttempts[player.UserId] = nil
end)
