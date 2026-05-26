# Steal-a-Brainrot Game Management System Setup Guide

This project consists of an Admin Panel dashboard written in Python Flask alongside custom Lua components for integration directly into Roblox Studio games.

## Component 1: Python Admin Dashboard Setup

1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd d:\pybuilds\steal-a-brainrot\admin-dashboard
   ```

2. Initialize virtual environment and install dependencies:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Launch the development server:
   ```powershell
   python run.py
   ```

4. Complete first-run setup by navigating to:
   [http://localhost:5000/setup](http://localhost:5000/setup)
   - Create your Superadmin account.

5. Sign in to your dashboard at:
   [http://localhost:5000/login](http://localhost:5000/login)

## Component 2: Roblox Studio Implementation

To deploy in your game:
1. Copy files under `roblox-scripts\client\` and put them inside `StarterGui` (ensure `ResetOnSpawn` is false).
2. Copy files under `roblox-scripts\server\` and put them in `ServerScriptService`.
3. In Roblox Studio, open **Game Settings** -> **Security** -> Enable **Allow HTTP Requests** and **Enable Studio Access to API Services**.
4. Configure your Webhook URL inside the dashboard admin panel settings page to receive live Discord updates.
