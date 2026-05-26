-- PrivateNotifierUI.lua
-- Place in a LocalScript under StarterGui -> ScreenGui

local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")

local localPlayer = Players.LocalPlayer
local PlayerGui = localPlayer:WaitForChild("PlayerGui")

-- Remote resources
local GetServerList = ReplicatedStorage:WaitForChild("GetServerList")
local JoinServer = ReplicatedStorage:WaitForChild("JoinServer")

-- Create the UI elements programmatically to ensure it works immediately
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "SAB_PrivateNotifier"
screenGui.ResetOnSpawn = false
screenGui.IgnoreGuiInset = true
screenGui.Parent = PlayerGui

-- Toggle Button (Floating)
local toggleBtn = Instance.new("TextButton")
toggleBtn.Name = "ToggleUI"
toggleBtn.Size = UDim2.new(0, 50, 0, 50)
toggleBtn.Position = UDim2.new(1, -60, 0.5, -25)
toggleBtn.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
toggleBtn.TextColor3 = Color3.fromRGB(249, 250, 251)
toggleBtn.Text = "SAB"
toggleBtn.Font = Enum.Font.GothamBold
toggleBtn.TextSize = 14
toggleBtn.BorderSizePixel = 0
toggleBtn.Parent = screenGui

local btnCorner = Instance.new("UICorner", toggleBtn)
btnCorner.CornerRadius = UDim.new(0, 25)

local btnStroke = Instance.new("UIStroke", toggleBtn)
btnStroke.Color = Color3.fromRGB(59, 130, 246)
btnStroke.Thickness = 1.5

-- Main Panel
local mainFrame = Instance.new("Frame")
mainFrame.Name = "MainFrame"
mainFrame.Size = UDim2.new(0, 680, 0, 420)
mainFrame.Position = UDim2.new(0.5, -340, 0.5, -210)
mainFrame.BackgroundColor3 = Color3.fromRGB(17, 24, 27)
mainFrame.BorderSizePixel = 0
mainFrame.Visible = false
mainFrame.Parent = screenGui

local mainCorner = Instance.new("UICorner", mainFrame)
mainCorner.CornerRadius = UDim.new(0, 12)

local mainStroke = Instance.new("UIStroke", mainFrame)
mainStroke.Color = Color3.fromRGB(30, 41, 59)
mainStroke.Thickness = 2

-- Header
local header = Instance.new("Frame")
header.Name = "Header"
header.Size = UDim2.new(1, 0, 0, 50)
header.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
header.BorderSizePixel = 0
header.Parent = mainFrame

local headerCorner = Instance.new("UICorner", header)
headerCorner.CornerRadius = UDim.new(0, 12)

-- Sub-bar header frame to clip rounded bottom corners of header
local headerClip = Instance.new("Frame")
headerClip.Name = "Clip"
headerClip.Size = UDim2.new(1, 0, 0, 10)
headerClip.Position = UDim2.new(0, 0, 1, -10)
headerClip.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
headerClip.BorderSizePixel = 0
headerClip.Parent = header

local title = Instance.new("TextLabel")
title.Name = "Title"
title.Size = UDim2.new(0, 200, 1, 0)
title.Position = UDim2.new(0, 20, 0, 0)
title.BackgroundTransparency = 1
title.Text = "PRIVATE NOTIFIER"
title.TextColor3 = Color3.fromRGB(249, 250, 251)
title.Font = Enum.Font.GothamBold
title.TextSize = 16
title.TextXAlignment = Enum.TextXAlignment.Left
title.Parent = header

-- Online status indicator
local statusLabel = Instance.new("Frame")
statusLabel.Name = "Status"
statusLabel.Size = UDim2.new(0, 90, 0, 30)
statusLabel.Position = UDim2.new(0, 180, 0.5, -15)
statusLabel.BackgroundColor3 = Color3.fromRGB(15, 23, 42)
statusLabel.Parent = header

local statusCorner = Instance.new("UICorner", statusLabel)
statusCorner.CornerRadius = UDim.new(0, 15)

local statusStroke = Instance.new("UIStroke", statusLabel)
statusStroke.Color = Color3.fromRGB(16, 185, 129)
statusStroke.Thickness = 1.5

local statusDot = Instance.new("Frame")
statusDot.Size = UDim2.new(0, 10, 0, 10)
statusDot.Position = UDim2.new(0, 10, 0.5, -5)
statusDot.BackgroundColor3 = Color3.fromRGB(16, 185, 129)
statusDot.BorderSizePixel = 0
statusDot.Parent = statusLabel

local statusDotCorner = Instance.new("UICorner", statusDot)
statusDotCorner.CornerRadius = UDim.new(0, 5)

local statusText = Instance.new("TextLabel")
statusText.Size = UDim2.new(1, -25, 1, 0)
statusText.Position = UDim2.new(0, 25, 0, 0)
statusText.BackgroundTransparency = 1
statusText.Text = "Online"
statusText.TextColor3 = Color3.fromRGB(16, 185, 129)
statusText.Font = Enum.Font.GothamBold
statusText.TextSize = 12
statusText.Parent = statusLabel

-- Close button
local closeBtn = Instance.new("TextButton")
closeBtn.Name = "Close"
closeBtn.Size = UDim2.new(0, 30, 0, 30)
closeBtn.Position = UDim2.new(1, -40, 0.5, -15)
closeBtn.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
closeBtn.TextColor3 = Color3.fromRGB(239, 68, 68)
closeBtn.Text = "X"
closeBtn.Font = Enum.Font.GothamBold
closeBtn.TextSize = 14
closeBtn.BorderSizePixel = 0
closeBtn.Parent = header

local closeCorner = Instance.new("UICorner", closeBtn)
closeCorner.CornerRadius = UDim.new(0, 15)

-- Sidebar
local sidebar = Instance.new("Frame")
sidebar.Name = "Sidebar"
sidebar.Size = UDim2.new(0, 180, 1, -50)
sidebar.Position = UDim2.new(0, 0, 0, 50)
sidebar.BackgroundColor3 = Color3.fromRGB(24, 24, 30)
sidebar.BorderSizePixel = 0
sidebar.Parent = mainFrame

local sidebarLayout = Instance.new("UIListLayout")
sidebarLayout.Padding = UDim.new(0, 8)
sidebarLayout.Parent = sidebar

local sidebarPadding = Instance.new("UIPadding")
sidebarPadding.PaddingLeft = UDim.new(0, 10)
sidebarPadding.PaddingRight = UDim.new(0, 10)
sidebarPadding.PaddingTop = UDim.new(0, 15)
sidebarPadding.Parent = sidebar

local function createTabButton(name, icon)
    local button = Instance.new("TextButton")
    button.Name = name .. "Tab"
    button.Size = UDim2.new(1, 0, 0, 40)
    button.BackgroundColor3 = Color3.fromRGB(31, 41, 55)
    button.TextColor3 = Color3.fromRGB(249, 250, 251)
    button.Text = icon .. "   " .. name
    button.Font = Enum.Font.GothamSemibold
    button.TextSize = 12
    button.TextXAlignment = Enum.TextXAlignment.Left
    button.BorderSizePixel = 0
    button.Parent = sidebar
    
    local corner = Instance.new("UICorner", button)
    corner.CornerRadius = UDim.new(0, 6)
    
    local padding = Instance.new("UIPadding", button)
    padding.PaddingLeft = UDim.new(0, 15)
    
    return button
end

local joinerTab = createTabButton("Joiner", "🏠")
local settingTab = createTabButton("Setting", "⚙️")
local miscTab = createTabButton("Misc", "📄")

-- Large Join Server Button at bottom left
local joinServerBtn = Instance.new("TextButton")
joinServerBtn.Name = "JoinServerBtn"
joinServerBtn.Size = UDim2.new(0, 160, 0, 40)
joinServerBtn.Position = UDim2.new(0, 10, 1, -50)
joinServerBtn.BackgroundColor3 = Color3.fromRGB(16, 185, 129)
joinServerBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
joinServerBtn.Text = "Join Server"
joinServerBtn.Font = Enum.Font.GothamBold
joinServerBtn.TextSize = 14
joinServerBtn.Parent = sidebar

local joinServerCorner = Instance.new("UICorner", joinServerBtn)
joinServerCorner.CornerRadius = UDim.new(0, 6)

-- Content Pane Container
local container = Instance.new("Frame")
container.Name = "Content"
container.Size = UDim2.new(1, -180, 1, -50)
container.Position = UDim2.new(0, 180, 0, 50)
container.BackgroundTransparency = 1
container.Parent = mainFrame

-- Joiner View (ScrollingFrame)
local joinerContent = Instance.new("ScrollingFrame")
joinerContent.Size = UDim2.new(1, -20, 1, -60)
joinerContent.Position = UDim2.new(0, 10, 0, 10)
joinerContent.BackgroundTransparency = 1
joinerContent.ScrollBarThickness = 6
joinerContent.ScrollBarImageColor3 = Color3.fromRGB(59, 130, 246)
joinerContent.Parent = container

local joinerLayout = Instance.new("UIListLayout")
joinerLayout.Padding = UDim.new(0, 10)
joinerLayout.Parent = joinerContent

-- Status Bar
local footerBar = Instance.new("Frame")
footerBar.Name = "Footer"
footerBar.Size = UDim2.new(1, -20, 0, 40)
footerBar.Position = UDim2.new(0, 10, 1, -45)
footerBar.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
footerBar.Parent = container

local footerCorner = Instance.new("UICorner", footerBar)
footerCorner.CornerRadius = UDim.new(0, 6)

local autoJoinText = Instance.new("TextLabel")
autoJoinText.Size = UDim2.new(1, -20, 1, 0)
autoJoinText.Position = UDim2.new(0, 15, 0, 0)
autoJoinText.BackgroundTransparency = 1
autoJoinText.Text = "⚫ Auto Joiner Inactive"
autoJoinText.TextColor3 = Color3.fromRGB(239, 68, 68)
autoJoinText.Font = Enum.Font.GothamBold
autoJoinText.TextSize = 12
autoJoinText.TextXAlignment = Enum.TextXAlignment.Left
autoJoinText.Parent = footerBar

-- Mock List Generation Function
local function populateServers(servers)
    for _, item in ipairs(joinerContent:GetChildren()) do
        if item:IsA("Frame") then item:Destroy() end
    end

    for _, srv in ipairs(servers) do
        local serverFrame = Instance.new("Frame")
        serverFrame.Size = UDim2.new(1, -10, 0, 70)
        serverFrame.BackgroundColor3 = Color3.fromRGB(31, 41, 55)
        serverFrame.Parent = joinerContent
        
        local corner = Instance.new("UICorner", serverFrame)
        corner.CornerRadius = UDim.new(0, 6)
        
        local thumbnail = Instance.new("ImageLabel")
        thumbnail.Size = UDim2.new(0, 50, 0, 50)
        thumbnail.Position = UDim2.new(0, 10, 0.5, -25)
        thumbnail.Image = "rbxassetid://109983668079237" -- Mock brainrot character
        thumbnail.BackgroundColor3 = Color3.fromRGB(24, 24, 30)
        thumbnail.Parent = serverFrame
        Instance.new("UICorner", thumbnail).CornerRadius = UDim.new(0, 6)
        
        local infoLabel = Instance.new("TextLabel")
        infoLabel.Size = UDim2.new(0, 250, 0, 20)
        infoLabel.Position = UDim2.new(0, 70, 0, 10)
        infoLabel.BackgroundTransparency = 1
        infoLabel.Text = srv.Name
        infoLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
        infoLabel.Font = Enum.Font.GothamBold
        infoLabel.TextSize = 13
        infoLabel.TextXAlignment = Enum.TextXAlignment.Left
        infoLabel.Parent = serverFrame

        -- Earning badge
        local rateBadge = Instance.new("TextLabel")
        rateBadge.Size = UDim2.new(0, 80, 0, 20)
        rateBadge.Position = UDim2.new(0, 70, 0, 35)
        rateBadge.BackgroundColor3 = Color3.fromRGB(6, 78, 59)
        rateBadge.Text = srv.Rate
        rateBadge.TextColor3 = Color3.fromRGB(52, 211, 153)
        rateBadge.Font = Enum.Font.GothamBold
        rateBadge.TextSize = 10
        rateBadge.Parent = serverFrame
        Instance.new("UICorner", rateBadge).CornerRadius = UDim.new(0, 10)

        -- nil tag
        local nilBadge = Instance.new("TextLabel")
        nilBadge.Size = UDim2.new(0, 40, 0, 20)
        nilBadge.Position = UDim2.new(0, 155, 0, 35)
        nilBadge.BackgroundColor3 = Color3.fromRGB(15, 23, 42)
        nilBadge.Text = "nil"
        nilBadge.TextColor3 = Color3.fromRGB(156, 163, 175)
        nilBadge.Font = Enum.Font.GothamBold
        nilBadge.TextSize = 10
        nilBadge.Parent = serverFrame
        Instance.new("UICorner", nilBadge).CornerRadius = UDim.new(0, 10)

        -- Players count
        local countBadge = Instance.new("TextLabel")
        countBadge.Size = UDim2.new(0, 50, 0, 25)
        countBadge.Position = UDim2.new(1, -160, 0.5, -12)
        countBadge.BackgroundColor3 = Color3.fromRGB(6, 78, 59)
        countBadge.Text = srv.Players .. "/8"
        countBadge.TextColor3 = Color3.fromRGB(52, 211, 153)
        countBadge.Font = Enum.Font.GothamBold
        countBadge.TextSize = 11
        countBadge.Parent = serverFrame
        Instance.new("UICorner", countBadge).CornerRadius = UDim.new(0, 12)

        -- Spam Join Button
        local joinBtn = Instance.new("TextButton")
        joinBtn.Size = UDim2.new(0, 90, 0, 30)
        joinBtn.Position = UDim2.new(1, -100, 0.5, -15)
        joinBtn.BackgroundColor3 = Color3.fromRGB(59, 130, 246)
        joinBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
        joinBtn.Text = "Spam Join"
        joinBtn.Font = Enum.Font.GothamBold
        joinBtn.TextSize = 11
        joinBtn.Parent = serverFrame
        
        Instance.new("UICorner", joinBtn).CornerRadius = UDim.new(0, 6)
        
        joinBtn.Activated:Connect(function()
            local success = JoinServer:InvokeServer(srv.AccessCode)
            if not success then
                StarterGui:SetCore("SendNotification", {
                    Title = "Failed teleport",
                    Text = "Server may be full or inaccessible.",
                    Duration = 3
                })
            end
        end)
    end
end

-- Interactions
toggleBtn.Activated:Connect(function()
    mainFrame.Visible = not mainFrame.Visible
    if mainFrame.Visible then
        mainFrame.Size = UDim2.new(0, 0, 0, 420)
        TweenService:Create(mainFrame, TweenInfo.new(0.4, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), {
            Size = UDim2.new(0, 680, 0, 420)
        }):Play()
        
        -- Load Servers
        local servers = GetServerList:InvokeServer()
        if servers then populateServers(servers) end
    end
end)

closeBtn.Activated:Connect(function()
    TweenService:Create(mainFrame, TweenInfo.new(0.3, Enum.EasingStyle.Quint, Enum.EasingDirection.In), {
        Size = UDim2.new(0, 0, 0, 420)
    }):Play()
    task.wait(0.3)
    mainFrame.Visible = false
end)

-- Mock list servers if empty
local mockServers = {
    { Name = "[Normal] Garama and Madundung", Rate = "$650M/s", Players = 2, AccessCode = "test1" },
    { Name = "[Normal] Mariachi Corazoni", Rate = "$125M/s", Players = 3, AccessCode = "test2" },
    { Name = "[Normal] Cooki and Milki", Rate = "$930M/s", Players = 2, AccessCode = "test3" },
    { Name = "[Normal] La Romantic Grande", Rate = "$540M/s", Players = 2, AccessCode = "test4" }
}
populateServers(mockServers)
