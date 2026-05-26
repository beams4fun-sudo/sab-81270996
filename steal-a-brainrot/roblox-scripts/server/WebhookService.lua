-- WebhookService.lua
-- Place in ServerScriptService

local HttpService = game:GetService("HttpService")

local WebhookService = {}

-- Change this config to your proxy endpoint
local PROXY_URL = "https://webhook.lewisakura.moe/api/webhooks/YOUR_ID/YOUR_TOKEN"

function WebhookService.sendEmbed(title, description, color_dec, fields)
    local payload = {
        embeds = {{
            title = title,
            description = description,
            color = color_dec or 3901686, -- Blue
            timestamp = os.date("!%Y-%m-%dT%H:%M:%S.000Z"),
            fields = fields or {}
        }}
    }
    
    local success, response = pcall(function()
        return HttpService:RequestAsync({
            Url = PROXY_URL,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = HttpService:JSONEncode(payload)
        })
    end)
    
    if not success then
        warn("Failed to deliver webhook embed: " .. tostring(response))
    end
end

function WebhookService.sendPlayerJoined(player)
    WebhookService.sendEmbed(
        "📥 Player Joined",
        player.Name .. " joined the experience.",
        65280, -- Green
        {
            {name = "User ID", value = tostring(player.UserId), inline = true}
        }
    )
end

function WebhookService.sendPlayerLeft(player)
    WebhookService.sendEmbed(
        "📤 Player Left",
        player.Name .. " left the experience.",
        16711680, -- Red
        {
            {name = "User ID", value = tostring(player.UserId), inline = true}
        }
    )
end

function WebhookService.sendTradeCompleted(player1Name, player2Name, itemsDetails)
    WebhookService.sendEmbed(
        "🔄 Trade Completed",
        player1Name .. " successfully completed a trade with " .. player2Name,
        9109759, -- Purple
        {
            {name = "Exchange Description", value = itemsDetails, inline = false}
        }
    )
end

return WebhookService
