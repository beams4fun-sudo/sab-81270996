-- BrainrotNotifier.lua
-- LocalScript placed under StarterGui -> ScreenGui

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Players = game:GetService("Players")

local localPlayer = Players.LocalPlayer
local PlayerGui = localPlayer:WaitForChild("PlayerGui")
local GameNotification = ReplicatedStorage:WaitForChild("GameNotification")

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "SAB_NotificationStack"
screenGui.ResetOnSpawn = false
screenGui.Parent = PlayerGui

local notificationContainer = Instance.new("Frame")
notificationContainer.Size = UDim2.new(0, 300, 1, 0)
notificationContainer.Position = UDim2.new(1, -310, 0, 0)
notificationContainer.BackgroundTransparency = 1
notificationContainer.Parent = screenGui

local layout = Instance.new("UIListLayout")
layout.Padding = UDim.new(0, 10)
layout.VerticalAlignment = Enum.VerticalAlignment.Bottom
layout.HorizontalAlignment = Enum.HorizontalAlignment.Right
layout.Parent = notificationContainer

local padding = Instance.new("UIPadding")
padding.PaddingBottom = UDim.new(0, 20)
padding.PaddingRight = UDim.new(0, 10)
padding.Parent = notificationContainer

local function triggerNotification(title, text, color_hex)
    local card = Instance.new("Frame")
    card.Size = UDim2.new(1, 0, 0, 70)
    card.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
    card.BorderSizePixel = 0
    card.BackgroundTransparency = 1 -- Animate entrance
    card.Parent = notificationContainer
    
    local corner = Instance.new("UICorner", card)
    corner.CornerRadius = UDim.new(0, 6)
    
    local hexVal = color_hex:gsub("#", "")
    local r = tonumber(hexVal:sub(1,2), 16) / 255
    local g = tonumber(hexVal:sub(3,4), 16) / 255
    local b = tonumber(hexVal:sub(5,6), 16) / 255
    local color = Color3.new(r, g, b)
    
    local leftBorder = Instance.new("Frame")
    leftBorder.Size = UDim2.new(0, 4, 1, 0)
    leftBorder.BackgroundColor3 = color
    leftBorder.BorderSizePixel = 0
    leftBorder.Parent = card
    Instance.new("UICorner", leftBorder).CornerRadius = UDim.new(0, 2)

    local titleLabel = Instance.new("TextLabel")
    titleLabel.Size = UDim2.new(1, -20, 0, 20)
    titleLabel.Position = UDim2.new(0, 15, 0, 10)
    titleLabel.BackgroundTransparency = 1
    titleLabel.Text = title
    titleLabel.TextColor3 = Color3.fromRGB(249, 250, 251)
    titleLabel.Font = Enum.Font.GothamBold
    titleLabel.TextSize = 12
    titleLabel.TextXAlignment = Enum.TextXAlignment.Left
    titleLabel.Parent = card

    local descLabel = Instance.new("TextLabel")
    descLabel.Size = UDim2.new(1, -20, 0, 30)
    descLabel.Position = UDim2.new(0, 15, 0, 30)
    descLabel.BackgroundTransparency = 1
    descLabel.Text = text
    descLabel.TextColor3 = Color3.fromRGB(156, 163, 175)
    descLabel.Font = Enum.Font.Gotham
    descLabel.TextSize = 11
    descLabel.TextWrapped = true
    descLabel.TextXAlignment = Enum.TextXAlignment.Left
    descLabel.Parent = card

    -- Entrance tween
    TweenService:Create(card, TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
        BackgroundTransparency = 0.05
    }):Play()

    -- Auto dismissal
    task.delay(4, function()
        local exit = TweenService:Create(card, TweenInfo.new(0.3, Enum.EasingStyle.Quint, Enum.EasingDirection.In), {
            BackgroundTransparency = 1,
            Size = UDim2.new(1, 0, 0, 0)
        })
        exit:Play()
        exit.Completed:Wait()
        card:Destroy()
    end)
end

GameNotification.OnClientEvent:Connect(function(title, text, color_hex)
    triggerNotification(title, text, color_hex)
end)
