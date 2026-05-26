-- KeyValidationUI.lua
-- LocalScript placed under StarterGui -> ScreenGui

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local localPlayer = Players.LocalPlayer
local PlayerGui = localPlayer:WaitForChild("PlayerGui")
local ValidateKey = ReplicatedStorage:WaitForChild("ValidateKey")

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "SAB_AccessKey"
screenGui.IgnoreGuiInset = true
screenGui.ResetOnSpawn = false
screenGui.Parent = PlayerGui

-- Background Overlay blur simulation
local overlay = Instance.new("Frame")
overlay.Size = UDim2.new(1, 0, 1, 0)
overlay.BackgroundColor3 = Color3.fromRGB(10, 14, 26)
overlay.BackgroundTransparency = 0.35
overlay.BorderSizePixel = 0
overlay.Parent = screenGui

-- validation Card
local card = Instance.new("Frame")
card.Size = UDim2.new(0, 400, 0, 250)
card.Position = UDim2.new(0.5, -200, 0.5, -125)
card.BackgroundColor3 = Color3.fromRGB(17, 24, 39)
card.BorderSizePixel = 0
card.Parent = overlay

local corner = Instance.new("UICorner", card)
corner.CornerRadius = UDim.new(0, 12)

local stroke = Instance.new("UIStroke", card)
stroke.Color = Color3.fromRGB(59, 130, 246)
stroke.Thickness = 1.5

local title = Instance.new("TextLabel")
title.Size = UDim2.new(1, 0, 0, 40)
title.Position = UDim2.new(0, 0, 0, 20)
title.BackgroundTransparency = 1
title.Text = "STEAL-A-BRAINROT"
title.TextColor3 = Color3.fromRGB(249, 250, 251)
title.Font = Enum.Font.GothamBold
title.TextSize = 18
title.Parent = card

local subtitle = Instance.new("TextLabel")
subtitle.Size = UDim2.new(1, 0, 0, 20)
subtitle.Position = UDim2.new(0, 0, 0, 50)
subtitle.BackgroundTransparency = 1
subtitle.Text = "Verify your system license key to play"
subtitle.TextColor3 = Color3.fromRGB(156, 163, 175)
subtitle.Font = Enum.Font.GothamSemibold
subtitle.TextSize = 12
subtitle.Parent = card

local keyInput = Instance.new("TextBox")
keyInput.Size = UDim2.new(0, 300, 0, 40)
keyInput.Position = UDim2.new(0.5, -150, 0, 95)
keyInput.BackgroundColor3 = Color3.fromRGB(31, 41, 55)
keyInput.TextColor3 = Color3.fromRGB(255, 255, 255)
keyInput.PlaceholderText = "SAB-XXXXXXXXXXXXXXXX"
keyInput.PlaceholderColor3 = Color3.fromRGB(107, 114, 128)
keyInput.Text = ""
keyInput.Font = Enum.Font.Code
keyInput.TextSize = 13
keyInput.BorderSizePixel = 0
keyInput.Parent = card

Instance.new("UICorner", keyInput).CornerRadius = UDim.new(0, 6)
local inputStroke = Instance.new("UIStroke", keyInput)
inputStroke.Color = Color3.fromRGB(55, 65, 81)
inputStroke.Thickness = 1

local statusLabel = Instance.new("TextLabel")
statusLabel.Size = UDim2.new(0, 300, 0, 20)
statusLabel.Position = UDim2.new(0.5, -150, 0, 145)
statusLabel.BackgroundTransparency = 1
statusLabel.Text = ""
statusLabel.TextColor3 = Color3.fromRGB(239, 68, 68)
statusLabel.Font = Enum.Font.Gotham
statusLabel.TextSize = 11
statusLabel.Parent = card

local validateBtn = Instance.new("TextButton")
validateBtn.Size = UDim2.new(0, 300, 0, 40)
validateBtn.Position = UDim2.new(0.5, -150, 0, 180)
validateBtn.BackgroundColor3 = Color3.fromRGB(16, 185, 129)
validateBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
validateBtn.Text = "VALIDATE LICENSE"
validateBtn.Font = Enum.Font.GothamBold
validateBtn.TextSize = 13
validateBtn.BorderSizePixel = 0
validateBtn.Parent = card

Instance.new("UICorner", validateBtn).CornerRadius = UDim.new(0, 6)

-- Click Handlers
validateBtn.Activated:Connect(function()
    local keyText = keyInput.Text:gsub("%s+", "")
    if #keyText == 0 then
        statusLabel.Text = "Please enter your key."
        statusLabel.TextColor3 = Color3.fromRGB(239, 68, 68)
        return
    end

    statusLabel.Text = "Validating key..."
    statusLabel.TextColor3 = Color3.fromRGB(59, 130, 246)
    validateBtn.Active = false

    local success, response = pcall(function()
        return ValidateKey:InvokeServer(keyText)
    end)

    validateBtn.Active = true

    if success and response and response.valid then
        statusLabel.Text = "Success! Access granted."
        statusLabel.TextColor3 = Color3.fromRGB(16, 185, 129)
        
        task.wait(1)
        
        -- Smooth fade transition
        local fadeTween = TweenService:Create(overlay, TweenInfo.new(0.5, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), {
            BackgroundTransparency = 1
        })
        TweenService:Create(card, TweenInfo.new(0.5, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), {
            BackgroundTransparency = 1
        }):Play()
        fadeTween:Play()
        fadeTween.Completed:Wait()
        screenGui:Destroy()
    else
        local errMsg = (response and response.message) or "Validation failed. Server unreachable."
        statusLabel.Text = errMsg
        statusLabel.TextColor3 = Color3.fromRGB(239, 68, 68)
        
        -- Shake animation on input box
        local originalPos = keyInput.Position
        for _ = 1, 5 do
            keyInput.Position = originalPos + UDim2.new(0, math.random(-5, 5), 0, 0)
            task.wait(0.02)
        end
        keyInput.Position = originalPos
    end
end)
