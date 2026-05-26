-- TradingUI.lua
-- LocalScript inside StarterGui -> ScreenGui

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local localPlayer = Players.LocalPlayer
local PlayerGui = localPlayer:WaitForChild("PlayerGui")

-- Remotes
local RequestTrade = ReplicatedStorage:WaitForChild("RequestTrade")
local AcceptTrade = ReplicatedStorage:WaitForChild("AcceptTrade")
local DeclineTrade = ReplicatedStorage:WaitForChild("DeclineTrade")
local TradeUpdate = ReplicatedStorage:WaitForChild("TradeUpdate")

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "SAB_TradingSystem"
screenGui.ResetOnSpawn = false
screenGui.Parent = PlayerGui

-- Trade Popup Invitation Notification
local popup = Instance.new("Frame")
popup.Name = "TradeInvitePopup"
popup.Size = UDim2.new(0, 300, 0, 100)
popup.Position = UDim2.new(1, 10, 0.1, 0) -- Hidden off right
popup.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
popup.BorderSizePixel = 0
popup.Parent = screenGui

Instance.new("UICorner", popup).CornerRadius = UDim.new(0, 8)
local stroke = Instance.new("UIStroke", popup)
stroke.Color = Color3.fromRGB(59, 130, 246)
stroke.Thickness = 1.5

local inviteLabel = Instance.new("TextLabel")
inviteLabel.Size = UDim2.new(1, -20, 0, 40)
inviteLabel.Position = UDim2.new(0, 10, 0, 10)
inviteLabel.BackgroundTransparency = 1
inviteLabel.Text = "Player sent you a trade request!"
inviteLabel.TextColor3 = Color3.fromRGB(249, 250, 251)
inviteLabel.Font = Enum.Font.GothamSemibold
inviteLabel.TextSize = 12
inviteLabel.TextWrapped = true
inviteLabel.Parent = popup

local acceptBtn = Instance.new("TextButton")
acceptBtn.Size = UDim2.new(0, 130, 0, 30)
acceptBtn.Position = UDim2.new(0, 10, 1, -40)
acceptBtn.BackgroundColor3 = Color3.fromRGB(16, 185, 129)
acceptBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
acceptBtn.Text = "Accept"
acceptBtn.Font = Enum.Font.GothamBold
acceptBtn.TextSize = 11
acceptBtn.Parent = popup
Instance.new("UICorner", acceptBtn).CornerRadius = UDim.new(0, 6)

local declineBtn = Instance.new("TextButton")
declineBtn.Size = UDim2.new(0, 130, 0, 30)
declineBtn.Position = UDim2.new(1, -140, 1, -40)
declineBtn.BackgroundColor3 = Color3.fromRGB(239, 68, 68)
declineBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
declineBtn.Text = "Decline"
declineBtn.Font = Enum.Font.GothamBold
declineBtn.TextSize = 11
declineBtn.Parent = popup
Instance.new("UICorner", declineBtn).CornerRadius = UDim.new(0, 6)

-- Trade Window
local window = Instance.new("Frame")
window.Name = "TradeWindow"
window.Size = UDim2.new(0, 600, 0, 350)
window.Position = UDim2.new(0.5, -300, 0.5, -175)
window.BackgroundColor3 = Color3.fromRGB(17, 24, 39)
window.BorderSizePixel = 0
window.Visible = false
window.Parent = screenGui

Instance.new("UICorner", window).CornerRadius = UDim.new(0, 12)
local windowStroke = Instance.new("UIStroke", window)
windowStroke.Color = Color3.fromRGB(59, 130, 246)
windowStroke.Thickness = 1.5

-- Columns Layout
local leftCol = Instance.new("Frame")
leftCol.Size = UDim2.new(0.5, -15, 1, -80)
leftCol.Position = UDim2.new(0, 10, 0, 20)
leftCol.BackgroundColor3 = Color3.fromRGB(31, 41, 55)
leftCol.Parent = window
Instance.new("UICorner", leftCol).CornerRadius = UDim.new(0, 6)

local rightCol = Instance.new("Frame")
rightCol.Size = UDim2.new(0.5, -15, 1, -80)
rightCol.Position = UDim2.new(0.5, 5, 0, 20)
rightCol.BackgroundColor3 = Color3.fromRGB(31, 41, 55)
rightCol.Parent = window
Instance.new("UICorner", rightCol).CornerRadius = UDim.new(0, 6)

local confirmBtn = Instance.new("TextButton")
confirmBtn.Size = UDim2.new(0, 200, 0, 40)
confirmBtn.Position = UDim2.new(0.5, -210, 1, -50)
confirmBtn.BackgroundColor3 = Color3.fromRGB(16, 185, 129)
confirmBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
confirmBtn.Text = "Confirm Trade"
confirmBtn.Font = Enum.Font.GothamBold
confirmBtn.TextSize = 14
confirmBtn.Parent = window
Instance.new("UICorner", confirmBtn).CornerRadius = UDim.new(0, 6)

local cancelBtn = Instance.new("TextButton")
cancelBtn.Size = UDim2.new(0, 200, 0, 40)
cancelBtn.Position = UDim2.new(0.5, 10, 1, -50)
cancelBtn.BackgroundColor3 = Color3.fromRGB(239, 68, 68)
cancelBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
cancelBtn.Text = "Cancel"
cancelBtn.Font = Enum.Font.GothamBold
cancelBtn.TextSize = 14
cancelBtn.Parent = window
Instance.new("UICorner", cancelBtn).CornerRadius = UDim.new(0, 6)

-- Handle Invitations from Server
local activeTradePartner = nil

TradeUpdate.OnClientEvent:Connect(function(event, partnerName)
    if event == "Request" then
        activeTradePartner = partnerName
        inviteLabel.Text = partnerName .. " wants to trade with you!"
        
        popup.Position = UDim2.new(1, 10, 0.1, 0)
        TweenService:Create(popup, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
            Position = UDim2.new(1, -310, 0.1, 0)
        }):Play()
    elseif event == "Start" then
        activeTradePartner = partnerName
        window.Visible = true
        popup.Visible = false
    elseif event == "Success" then
        window.Visible = false
        activeTradePartner = nil
        game:GetService("StarterGui"):SetCore("SendNotification", {
            Title = "Trade Successful!",
            Text = "Items have been transferred.",
            Duration = 5
        })
    elseif event == "Cancelled" then
        window.Visible = false
        activeTradePartner = nil
        game:GetService("StarterGui"):SetCore("SendNotification", {
            Title = "Trade Cancelled",
            Text = "The trade session ended.",
            Duration = 3
        })
    end
end)

acceptBtn.Activated:Connect(function()
    if activeTradePartner then
        AcceptTrade:FireServer(activeTradePartner)
        TweenService:Create(popup, TweenInfo.new(0.3, Enum.EasingStyle.Quint, Enum.EasingDirection.In), {
            Position = UDim2.new(1, 10, 0.1, 0)
        }):Play()
    end
end)

declineBtn.Activated:Connect(function()
    if activeTradePartner then
        DeclineTrade:FireServer(activeTradePartner)
        TweenService:Create(popup, TweenInfo.new(0.3, Enum.EasingStyle.Quint, Enum.EasingDirection.In), {
            Position = UDim2.new(1, 10, 0.1, 0)
        }):Play()
    end
end)

confirmBtn.Activated:Connect(function()
    ReplicatedStorage.ConfirmTrade:FireServer()
end)

cancelBtn.Activated:Connect(function()
    ReplicatedStorage.DeclineTrade:FireServer(activeTradePartner)
end)
