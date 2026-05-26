#!/usr/bin/env python
# sab_cli.py
# Premium, aesthetic terminal-based command console for Steal-a-Brainrot

import sys
import os
import argparse
from datetime import datetime

# Enforce UTF-8 console output to prevent CP1252 encoding crashes on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import create_app
from app.models import db, Key, User, ActivityLog, Settings, ScriptConfig
from app.services import key_service, webhook_service, script_config_service

# ANSI Escape Sequences for Premium Theme (Cyberpunk Dark Mode)
CLR_BLUE = "\033[38;5;39m"
CLR_CYAN = "\033[38;5;51m"
CLR_GREEN = "\033[38;5;48m"
CLR_YELLOW = "\033[38;5;220m"
CLR_RED = "\033[38;5;196m"
CLR_PURPLE = "\033[38;5;99m"
CLR_PINK = "\033[38;5;201m"
CLR_GRAY = "\033[38;5;244m"
CLR_BG_DARK = "\033[48;5;234m"
CLR_BOLD = "\033[1m"
CLR_UNDERLINE = "\033[4m"
CLR_RESET = "\033[0m"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = f"""
{CLR_BLUE}{CLR_BOLD}  +--------------------------------------------------------+
  |    {CLR_PINK}____  _____ _____  _    _       ____   ____   ___ _____  {CLR_BLUE}|
  |   {CLR_PINK}/ ___||_   _| ____|/ \\  | |     | __ ) |  _ \\ / _ \\_   _| {CLR_BLUE}|
  |   {CLR_PINK}\\___ \\  | | |  _| / _ \\ | |     |  _ \\ | |_) | | | || |   {CLR_BLUE}|
  |    {CLR_PINK}___) | | | | |__/ ___ \\| |___  | |_) ||  _ <| |_| || |   {CLR_BLUE}|
  |   {CLR_PINK}|____/  |_| |_____/_/   \\_\\_____| |____/ |_| \\_\\\\___/ |_|   {CLR_BLUE}|
  |                                                        |
  |             {CLR_CYAN}{CLR_BOLD}SYSTEM ADMINISTRATION & AUDIT SYSTEM{CLR_RESET}{CLR_BLUE}       |
  +--------------------------------------------------------+{CLR_RESET}"""
    print(banner)


def draw_box_top(title, width=60, color=CLR_BLUE):
    padding = width - len(title) - 4
    print(f"  {color}+-- {CLR_BOLD}{CLR_RESET}{title} {color}{'-' * padding}+{CLR_RESET}")

def draw_box_bottom(width=60, color=CLR_BLUE):
    print(f"  {color}+{'-' * (width - 2)}+{CLR_RESET}")

def print_row(label, value, color=CLR_RESET, box_color=CLR_BLUE):
    line = f"  {box_color}|{CLR_RESET}  {CLR_BOLD}{label:<22}{CLR_RESET} {color}{value:<30}{CLR_RESET}{box_color}|{CLR_RESET}"
    print(line)

def prompt_input(label, default_val=None, width=60):
    title = "USER INPUT"
    padding = width - len(title) - 6
    print(f"  {CLR_CYAN}+-- {CLR_BOLD}{CLR_RESET}{title} {CLR_CYAN}{'-' * padding}+{CLR_RESET}")
    
    prompt_str = f"  {CLR_CYAN}|{CLR_RESET}  {CLR_BOLD}{label}{CLR_RESET}"
    if default_val is not None:
        prompt_str += f" ({CLR_GRAY}{default_val}{CLR_RESET})"
    prompt_str += " > "
    
    val = input(prompt_str).strip()
    print(f"  {CLR_CYAN}+{'-' * (width - 2)}+{CLR_RESET}")
    
    if not val and default_val is not None:
        return default_val
    return val



def get_db_stats():
    stats = key_service.get_stats()
    draw_box_top("SYSTEM METRICS & HEALTH", 60, CLR_BLUE)
    
    print_row("Total Licenses", f"{stats['total_keys']} generated", CLR_BLUE)
    print_row("Active Licenses", f"{stats['active_keys']} active", CLR_GREEN)
    print_row("Unused Keys", f"{stats['unused_keys']} available", CLR_CYAN)
    print_row("Expired Licenses", f"{stats['expired_keys']} expired", CLR_YELLOW)
    print_row("Registered Members", f"{stats['total_users']} total players", CLR_PURPLE)
    print_row("Events (Today)", f"{stats['events_today']} events logged", CLR_PINK)
    
    draw_box_bottom(60, CLR_BLUE)

def list_keys():
    keys = Key.query.order_by(Key.created_at.desc()).all()
    
    draw_box_top("LICENSES REGISTRY", 96, CLR_CYAN)
    header = f"  {CLR_CYAN}|  {CLR_BOLD}{'ID':<4} | {'License Key / Preview':<36} | {'Status':<10} | {'Term':<5} | {'Registered User':<20}{CLR_RESET} {CLR_CYAN}|{CLR_RESET}"
    print(header)
    print(f"  {CLR_CYAN}+------+--------------------------------------+------------+-------+----------------------+{CLR_RESET}")
    
    for k in keys:
        status_color = CLR_RESET
        if k.status == 'active': status_color = CLR_GREEN
        elif k.status == 'unused': status_color = CLR_CYAN
        elif k.status == 'expired': status_color = CLR_YELLOW
        elif k.status == 'banned': status_color = CLR_RED
        
        user_str = k.user.username if k.user else "Unassigned"
        key_disp = k.key_string or k.key_preview
        
        row = f"  {CLR_CYAN}|{CLR_RESET}  {k.id:<4} {CLR_CYAN}|{CLR_RESET} {CLR_BOLD}{key_disp:<36}{CLR_RESET} {CLR_CYAN}|{CLR_RESET} {status_color}{k.status:<10}{CLR_RESET} {CLR_CYAN}|{CLR_RESET} {k.duration_days:<5} {CLR_CYAN}|{CLR_RESET} {user_str:<20} {CLR_CYAN}|{CLR_RESET}"
        print(row)
        
    draw_box_bottom(96, CLR_CYAN)

def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    
    draw_box_top("USER DIRECTORY & HWID BINDINGS", 96, CLR_PURPLE)
    header = f"  {CLR_PURPLE}|  {CLR_BOLD}{'ID':<4} | {'Username':<18} | {'Roblox ID':<12} | {'Status':<9} | {'IP Address':<15} | {'HWID Binding'}{CLR_RESET} {CLR_PURPLE}|{CLR_RESET}"
    print(header)
    print(f"  {CLR_PURPLE}+------+--------------------+--------------+-----------+-----------------+------------------+{CLR_RESET}")
    
    for u in users:
        status_color = CLR_GREEN if u.status == 'active' else CLR_RED
        row = f"  {CLR_PURPLE}|{CLR_RESET}  {u.id:<4} {CLR_PURPLE}|{CLR_RESET} {CLR_BOLD}{u.username:<18}{CLR_RESET} {CLR_PURPLE}|{CLR_RESET} {u.roblox_id or 'N/A':<12} {CLR_PURPLE}|{CLR_RESET} {status_color}{u.status:<9}{CLR_RESET} {CLR_PURPLE}|{CLR_RESET} {u.ip_address or 'N/A':<15} {CLR_PURPLE}|{CLR_RESET} {u.hwid or 'None':<18} {CLR_PURPLE}|{CLR_RESET}"
        print(row)
        
    draw_box_bottom(96, CLR_PURPLE)

def list_logs(limit=20):
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    
    draw_box_top("SYSTEM ACTIVITY AUDIT TRAIL", 96, CLR_PINK)
    header = f"  {CLR_PINK}|  {CLR_BOLD}{'Timestamp (UTC)':<19} | {'Event Type':<20} | {'Origin IP':<15} | {'Event Payload Description'}{CLR_RESET} {CLR_PINK}|{CLR_RESET}"
    print(header)
    print(f"  {CLR_PINK}+----------------------+----------------------+-----------------+----------------------------------+{CLR_RESET}")
    
    for l in logs:
        event_color = CLR_RESET
        if "FAILED" in l.event_type or "MISMATCH" in l.event_type: event_color = CLR_RED
        elif "ACTIVATED" in l.event_type or "SUCCESS" in l.event_type: event_color = CLR_GREEN
        elif "GENERATED" in l.event_type: event_color = CLR_BLUE
        
        time_str = l.created_at.strftime('%Y-%m-%d %H:%M:%S')
        details = (l.details or "")[:32] + "..." if len(l.details or "") > 32 else (l.details or "")
        
        row = f"  {CLR_PINK}|{CLR_RESET}  {time_str:<19} {CLR_PINK}|{CLR_RESET} {event_color}{l.event_type:<20}{CLR_RESET} {CLR_PINK}|{CLR_RESET} {l.ip_address or 'System':<15} {CLR_PINK}|{CLR_RESET} {details:<32} {CLR_PINK}|{CLR_RESET}"
        print(row)
        
    draw_box_bottom(96, CLR_PINK)

def generate_new_keys(count, duration, note):
    print(f"\n  {CLR_CYAN}>> Initializing Key Generation Sequence...{CLR_RESET}")
    keys = key_service.generate_key(
        duration_days=duration,
        created_by_id=None,
        note=note,
        count=count
    )
    
    draw_box_top("GENERATED ACCESS LICENSES", 60, CLR_GREEN)
    for k in keys:
        print_row("License Generated", k, CLR_BLUE, CLR_GREEN)
    draw_box_bottom(60, CLR_GREEN)
    print(f"\n  {CLR_YELLOW}[WARNING] Write down these keys. Plaintext values are only displayed once.{CLR_RESET}")

def perform_revoke(key_id):
    if key_service.revoke_key(key_id, admin_id=None):
        webhook_service.send_admin_action("CLI_Admin", "REVOKED_KEY", f"Key ID: {key_id}")
        print(f"\n  {CLR_GREEN}[v] Successfully revoked Key ID: {key_id}{CLR_RESET}")
    else:
        print(f"\n  {CLR_RED}[x] Failed to locate key or execute revoke for Key ID: {key_id}{CLR_RESET}")

def perform_ban(key_id):
    if key_service.ban_key(key_id, admin_id=None):
        webhook_service.send_admin_action("CLI_Admin", "BANNED_KEY", f"Key ID: {key_id}")
        print(f"\n  {CLR_GREEN}[v] Key ID: {key_id} has been banned. Linked HWID blacklist complete.{CLR_RESET}")
    else:
        print(f"\n  {CLR_RED}[x] Key ID: {key_id} ban operation failed.{CLR_RESET}")

def generate_keys_interactive():
    draw_box_top("INTERACTIVE LICENSE GENERATOR", 60, CLR_GREEN)
    print(f"  {CLR_GREEN}|{CLR_RESET}  Configure license terms for the new batch.             {CLR_GREEN}|{CLR_RESET}")
    draw_box_bottom(60, CLR_GREEN)
    
    try:
        count_str = prompt_input("Quantity of keys to generate", "1", 60)
        count = int(count_str) if count_str.isdigit() else 1
        
        days_str = prompt_input("License term duration (days)", "30", 60)
        duration = int(days_str) if days_str.isdigit() else 30
        
        note = prompt_input("Admin metadata note", "CLI Interactive Gen", 60)
        
        generate_new_keys(count, duration, note)
    except Exception as e:
        print(f"  {CLR_RED}[x] Key generation aborted or failed: {e}{CLR_RESET}")

def configure_webhook():
    draw_box_top("DISCORD WEBHOOK CONFIGURATION", 60, CLR_PURPLE)
    current_url = Settings.get('discord_webhook_url', '')
    url_preview = (current_url[:35] + "...") if current_url else "Not configured"
    print_row("Current Webhook", url_preview, CLR_CYAN, CLR_PURPLE)
    draw_box_bottom(60, CLR_PURPLE)
    
    new_url = prompt_input("Enter New Webhook URL (leave empty to skip)", None, 60)
    if new_url:
        Settings.set('discord_webhook_url', new_url)
        print(f"\n  {CLR_GREEN}[v] Webhook URL updated successfully in database!{CLR_RESET}")
        print(f"  {CLR_CYAN}>> Dispatching test embed to Discord...{CLR_RESET}")
        test_delivered = webhook_service.send_webhook(
            title="⚙️ CLI Webhook Configured",
            description="The administration command console has successfully updated the webhook receiver URL.",
            color_hex="8b5cf6",
            fields=[
                {"name": "Trigger Source", "value": "SAB CLI Admin Tool", "inline": True},
                {"name": "Connection Status", "value": "✓ Active Connection", "inline": True}
            ]
        )
        if test_delivered:
            print(f"  {CLR_GREEN}[v] Test embed delivered successfully to Discord!{CLR_RESET}")
        else:
            print(f"  {CLR_RED}[x] Failed to deliver test embed. Verify webhook URL is valid.{CLR_RESET}")

def member_portal():

    draw_box_top("MEMBER GATEWAY VALIDATION", 60, CLR_PURPLE)
    print(f"  {CLR_PURPLE}|{CLR_RESET}  Please enter your verification details below.                 {CLR_PURPLE}|{CLR_RESET}")
    draw_box_bottom(60, CLR_PURPLE)

    
    try:
        key_str = prompt_input("License Key", None, 60)
        if not key_str:
            print(f"  {CLR_RED}[x] Error: Key parameter cannot be null.{CLR_RESET}")
            return
            
        hwid_str = prompt_input("Hardware ID", "CLI_Device_1", 60)

            
        print(f"\n  {CLR_CYAN}>> Dispatched verification payload to server endpoint...{CLR_RESET}")
        
        import requests
        url = 'http://localhost:5000/api/validate'
        payload = {
            'key': key_str,
            'hwid': hwid_str,
            'player_id': '99999',
            'player_name': 'CLI_Member'
        }
        
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                draw_box_top("[v] VERIFICATION GRANTED", 60, CLR_GREEN)
                print_row("Status", "SUCCESS", CLR_GREEN, CLR_GREEN)
                print_row("Expires At", data.get('expires_at'), CLR_BLUE, CLR_GREEN)
                print_row("Callback Message", data.get('message'), CLR_RESET, CLR_GREEN)
                draw_box_bottom(60, CLR_GREEN)
            else:
                draw_box_top("[x] VERIFICATION REJECTED", 60, CLR_RED)
                print_row("Status", "DENIED", CLR_RED, CLR_RED)
                print_row("Reason", data.get('message'), CLR_YELLOW, CLR_RED)
                draw_box_bottom(60, CLR_RED)
        else:
            print(f"  {CLR_RED}[x] HTTP Error: Server responded with status code {response.status_code}{CLR_RESET}")
            
    except Exception as e:
        print(f"  {CLR_RED}[x] Connection Error: Could not connect to API server. ({e}){CLR_RESET}")

def roblox_lookup():
    draw_box_top("ROBLOX PLAYER RECONNAISSANCE", 60, CLR_CYAN)
    print(f"  {CLR_CYAN}|{CLR_RESET}  Search any Roblox user by username. No auth needed.        {CLR_CYAN}|{CLR_RESET}")
    draw_box_bottom(60, CLR_CYAN)

    try:
        username = prompt_input("Roblox Username", None, 60)
        if not username:
            print(f"  {CLR_RED}[x] Error: Username cannot be empty.{CLR_RESET}")
            return

        print(f"\n  {CLR_CYAN}>> Querying Roblox Users API...{CLR_RESET}")

        import requests
        r = requests.get('http://localhost:5000/api/roblox/search-username', params={'username': username}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            user = data.get('user', {})
            pres = data.get('presence', {})

            status_color = CLR_GREEN if pres.get('status') == 'Online' or pres.get('status') == 'In-Game' else CLR_GRAY

            draw_box_top("PLAYER PROFILE", 60, CLR_BLUE)
            print_row("Display Name", user.get('display_name', 'N/A'), CLR_BOLD, CLR_BLUE)
            print_row("Username", user.get('name', 'N/A'), CLR_CYAN, CLR_BLUE)
            print_row("User ID", str(user.get('id', 'N/A')), CLR_YELLOW, CLR_BLUE)
            print_row("Account Created", (user.get('created') or 'N/A')[:10], CLR_GRAY, CLR_BLUE)
            print_row("Banned", str(user.get('is_banned', False)), CLR_RED if user.get('is_banned') else CLR_GREEN, CLR_BLUE)
            print_row("Verified Badge", str(user.get('has_verified_badge', False)), CLR_PURPLE, CLR_BLUE)
            draw_box_bottom(60, CLR_BLUE)

            draw_box_top("PRESENCE STATUS", 60, CLR_GREEN)
            print_row("Status", pres.get('status', 'Unknown'), status_color, CLR_GREEN)
            print_row("Last Location", pres.get('last_location') or 'Hidden', CLR_GRAY, CLR_GREEN)
            print_row("Place ID", str(pres.get('place_id') or 'Hidden'), CLR_GRAY, CLR_GREEN)
            draw_box_bottom(60, CLR_GREEN)

            print(f"\n  {CLR_GRAY}Profile: {user.get('profile_url', 'N/A')}{CLR_RESET}")
        elif r.status_code == 404:
            print(f"\n  {CLR_RED}[x] No Roblox user found with that username.{CLR_RESET}")
        else:
            err = r.json().get('message', 'Unknown error')
            print(f"\n  {CLR_RED}[x] API Error: {err}{CLR_RESET}")
    except Exception as e:
        print(f"  {CLR_RED}[x] Connection Error: {e}{CLR_RESET}")

def inventory_monitor():
    draw_box_top("BRAINROT INVENTORY MONITOR", 60, CLR_PURPLE)
    print(f"  {CLR_PURPLE}|{CLR_RESET}  Check what brainrots a player has collected.             {CLR_PURPLE}|{CLR_RESET}")
    draw_box_bottom(60, CLR_PURPLE)

    try:
        player_id = prompt_input("Player ID to check", "530380818", 60)
        if not player_id:
            print(f"  {CLR_RED}[x] Error: Player ID is required.{CLR_RESET}")
            return

        print(f"\n  {CLR_CYAN}>> Fetching inventory data...{CLR_RESET}")

        import requests
        r = requests.get('http://localhost:5000/api/roblox/inventory/check', params={'player_id': player_id}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            pct = data.get('completion_pct', 0)

            # ASCII progress bar
            filled = int(pct / 5)
            bar = '#' * filled + '-' * (20 - filled)

            draw_box_top("COLLECTION STATUS", 60, CLR_GREEN)
            print_row("Player", data.get('player_name', 'Unknown'), CLR_BOLD, CLR_GREEN)
            print_row("Player ID", player_id, CLR_CYAN, CLR_GREEN)
            print_row("Owned", f"{data.get('count_owned', 0)}/{data.get('total', 0)}", CLR_BLUE, CLR_GREEN)
            print_row("Missing", str(data.get('count_missing', 0)), CLR_RED, CLR_GREEN)
            print_row("Completion", f"[{bar}] {pct}%", CLR_YELLOW, CLR_GREEN)
            print_row("Last Updated", data.get('last_updated', 'N/A')[:19], CLR_GRAY, CLR_GREEN)
            draw_box_bottom(60, CLR_GREEN)

            # Show owned items
            owned = data.get('owned_items', [])
            if owned:
                draw_box_top(f"OWNED BRAINROTS ({len(owned)})", 60, CLR_BLUE)
                for item in owned[:20]:
                    print_row("", item, CLR_GREEN, CLR_BLUE)
                if len(owned) > 20:
                    print_row("", f"... and {len(owned) - 20} more", CLR_GRAY, CLR_BLUE)
                draw_box_bottom(60, CLR_BLUE)

            # Show missing (first 10)
            missing = data.get('missing_items', [])
            if missing:
                draw_box_top(f"MISSING BRAINROTS ({len(missing)})", 60, CLR_RED)
                for item in missing[:10]:
                    print_row("", item, CLR_YELLOW, CLR_RED)
                if len(missing) > 10:
                    print_row("", f"... and {len(missing) - 10} more", CLR_GRAY, CLR_RED)
                draw_box_bottom(60, CLR_RED)
        elif r.status_code == 404:
            print(f"\n  {CLR_YELLOW}[!] No inventory data found for player {player_id}.{CLR_RESET}")
            print(f"  {CLR_GRAY}    The game server has not reported inventory for this player yet.{CLR_RESET}")
        else:
            err = r.json().get('message', 'Unknown error')
            print(f"\n  {CLR_RED}[x] API Error: {err}{CLR_RESET}")
    except Exception as e:
        print(f"  {CLR_RED}[x] Connection Error: {e}{CLR_RESET}")


def list_script_configs():
    configs = script_config_service.list_configs()
    draw_box_top("LUA SCRIPT CONFIGURATIONS", 96, CLR_BLUE)
    header = f"  {CLR_BLUE}|  {CLR_BOLD}{'ID':<4} | {'Label':<20} | {'Secret Key (Start)':<18} | {'Target Display (ID)':<28} | {'Delays':<10}{CLR_RESET} {CLR_BLUE}|{CLR_RESET}"
    print(header)
    print(f"  {CLR_BLUE}+------+----------------------+--------------------+------------------------------+------------+{CLR_RESET}")
    for c in configs:
        summary = script_config_service.get_config_summary(c)
        target_str = "None"
        if summary['target_name']:
            target_str = f"{summary['target_name']} ({summary['target_id']})"
        if len(target_str) > 28:
            target_str = target_str[:25] + "..."
        
        secret_start = summary['secret_key'][:15] + "..."
        delays_str = f"{summary['delay_step']}s/{summary['trade_cycle_delay']}s"
        
        row = f"  {CLR_BLUE}|{CLR_RESET}  {summary['id']:<4} {CLR_BLUE}|{CLR_RESET} {CLR_BOLD}{summary['label']:<20}{CLR_RESET} {CLR_BLUE}|{CLR_RESET} {CLR_CYAN}{secret_start:<18}{CLR_RESET} {CLR_BLUE}|{CLR_RESET} {CLR_GREEN}{target_str:<28}{CLR_RESET} {CLR_BLUE}|{CLR_RESET} {delays_str:<10} {CLR_BLUE}|{CLR_RESET}"
        print(row)
    draw_box_bottom(96, CLR_BLUE)


def create_script_config_interactive():
    draw_box_top("CREATE NEW SCRIPT CONFIG", 60, CLR_GREEN)
    print(f"  {CLR_GREEN}|{CLR_RESET}  Generate a custom Lua script loader key & configuration.  {CLR_GREEN}|{CLR_RESET}")
    draw_box_bottom(60, CLR_GREEN)
    
    label = prompt_input("Config Label / User Name", None, 60)
    if not label:
        print(f"  {CLR_RED}[x] Error: Label is required.{CLR_RESET}")
        return
        
    target_username = prompt_input("Target Roblox Username (Optional)", "", 60)
    delay_step_str = prompt_input("Delay Step (seconds)", "1", 60)
    trade_delay_str = prompt_input("Trade Cycle Delay (seconds)", "2", 60)
    
    delay_step = int(delay_step_str) if delay_step_str.isdigit() else 1
    trade_delay = int(trade_delay_str) if trade_delay_str.isdigit() else 2
    
    print(f"\n  {CLR_CYAN}>> Generating script configuration...{CLR_RESET}")
    try:
        config = script_config_service.create_config(
            label=label,
            target_username=target_username if target_username else None,
            delay_step=delay_step,
            trade_cycle_delay=trade_delay
        )
        
        draw_box_top("CONFIG GENERATION SUCCESSFUL", 60, CLR_GREEN)
        print_row("ID", str(config.id), CLR_BOLD, CLR_GREEN)
        print_row("Label", config.label, CLR_BLUE, CLR_GREEN)
        print_row("Secret Key", config.secret_key, CLR_CYAN, CLR_GREEN)
        print_row("Target Display", config.target_name or "None", CLR_GREEN, CLR_GREEN)
        print_row("Target ID", config.target_id or "None", CLR_GREEN, CLR_GREEN)
        draw_box_bottom(60, CLR_GREEN)
        
        print(f"\n  {CLR_YELLOW}[IMPORTANT] Dynamic loader URL: http://localhost:5000/api/scripts/loader/{config.secret_key}{CLR_RESET}")
    except Exception as e:
        print(f"  {CLR_RED}[x] Failed to create script config: {e}{CLR_RESET}")


def edit_config_target_interactive():
    list_script_configs()
    config_id_str = prompt_input("Enter Config ID to update", None, 60)
    if not config_id_str.isdigit():
        print(f"  {CLR_RED}[x] Error: Invalid Config ID.{CLR_RESET}")
        return
    config_id = int(config_id_str)
    
    target_username = prompt_input("Enter New Roblox Username to target", None, 60)
    if not target_username:
        print(f"  {CLR_RED}[x] Error: Username cannot be empty.{CLR_RESET}")
        return
        
    print(f"\n  {CLR_CYAN}>> Resolving user and updating config target...{CLR_RESET}")
    config, msg = script_config_service.set_target(config_id, target_username)
    if config:
        print(f"  {CLR_GREEN}[v] {msg}{CLR_RESET}")
    else:
        print(f"  {CLR_RED}[x] {msg}{CLR_RESET}")


def toggle_brainrots_interactive():
    list_script_configs()
    config_id_str = prompt_input("Enter Config ID to toggle brainrots for", None, 60)
    if not config_id_str.isdigit():
        print(f"  {CLR_RED}[x] Error: Invalid Config ID.{CLR_RESET}")
        return
    config_id = int(config_id_str)
    
    config = ScriptConfig.query.get(config_id)
    if not config:
        print(f"  {CLR_RED}[x] Error: Config not found.{CLR_RESET}")
        return
        
    summary = script_config_service.get_config_summary(config)
    
    draw_box_top(f"BRAINROT TOGGLE MENU (ID: {config_id})", 60, CLR_CYAN)
    print_row("Enabled Items", f"{summary['brainrots_enabled']}/{summary['brainrots_total']}", CLR_GREEN, CLR_CYAN)
    print_row("1. Toggle Single Item", "Modify specific brainrot status", CLR_RESET, CLR_CYAN)
    print_row("2. Toggle Category", "Toggle OG, SECRET, or ANTOH groups", CLR_RESET, CLR_CYAN)
    print_row("3. Toggle ALL ON", "Enable all 228 items", CLR_RESET, CLR_CYAN)
    print_row("4. Toggle ALL OFF", "Disable all 228 items", CLR_RESET, CLR_CYAN)
    print_row("5. Back to Script Menu", "Cancel operation", CLR_RESET, CLR_CYAN)
    draw_box_bottom(60, CLR_CYAN)
    
    choice = prompt_input("Select action (1-5)", None, 60)
    if choice == "1":
        item_name = prompt_input("Enter exact Brainrot Item Name", None, 60)
        from app.services.brainrot_catalog import is_valid_brainrot
        if not is_valid_brainrot(item_name):
            print(f"  {CLR_RED}[x] Error: '{item_name}' is not in the master brainrot catalog.{CLR_RESET}")
            return
        state_str = prompt_input("Status (1 for ENABLED / 0 for DISABLED)", "1", 60)
        enabled = state_str == "1"
        config, msg = script_config_service.toggle_brainrot(config_id, item_name, enabled)
        if config:
            print(f"  {CLR_GREEN}[v] {msg}{CLR_RESET}")
        else:
            print(f"  {CLR_RED}[x] {msg}{CLR_RESET}")
    elif choice == "2":
        cat = prompt_input("Enter Category Name (OG / SECRET / ANTOH)", None, 60)
        if cat.lower() not in ['og', 'secret', 'antoh']:
            print(f"  {CLR_RED}[x] Error: Invalid category name.{CLR_RESET}")
            return
        state_str = prompt_input("Status (1 for ENABLED / 0 for DISABLED)", "1", 60)
        enabled = state_str == "1"
        config, msg = script_config_service.toggle_category(config_id, cat, enabled)
        if config:
            print(f"  {CLR_GREEN}[v] {msg}{CLR_RESET}")
        else:
            print(f"  {CLR_RED}[x] {msg}{CLR_RESET}")
    elif choice == "3":
        config, msg = script_config_service.bulk_toggle(config_id, True)
        if config:
            print(f"  {CLR_GREEN}[v] {msg}{CLR_RESET}")
        else:
            print(f"  {CLR_RED}[x] {msg}{CLR_RESET}")
    elif choice == "4":
        config, msg = script_config_service.bulk_toggle(config_id, False)
        if config:
            print(f"  {CLR_GREEN}[v] {msg}{CLR_RESET}")
        else:
            print(f"  {CLR_RED}[x] {msg}{CLR_RESET}")


def rotate_config_key_interactive():
    list_script_configs()
    config_id_str = prompt_input("Enter Config ID to rotate key", None, 60)
    if not config_id_str.isdigit():
        print(f"  {CLR_RED}[x] Error: Invalid Config ID.{CLR_RESET}")
        return
    config_id = int(config_id_str)
    
    print(f"\n  {CLR_CYAN}>> Generating new secret key...{CLR_RESET}")
    config, msg = script_config_service.update_secret_key(config_id)
    if config:
        print(f"  {CLR_GREEN}[v] {msg}{CLR_RESET}")
        print(f"  {CLR_YELLOW}[IMPORTANT] New loader URL: http://localhost:5000/api/scripts/loader/{config.secret_key}{CLR_RESET}")
    else:
        print(f"  {CLR_RED}[x] {msg}{CLR_RESET}")


def view_loader_details_interactive():
    list_script_configs()
    config_id_str = prompt_input("Enter Config ID to view loader details", None, 60)
    if not config_id_str.isdigit():
        print(f"  {CLR_RED}[x] Error: Invalid Config ID.{CLR_RESET}")
        return
    view_loader_details_interactive_by_id(int(config_id_str))


def view_loader_details_interactive_by_id(config_id):
    config = ScriptConfig.query.get(config_id)
    if not config:
        print(f"  {CLR_RED}[x] Error: Config not found.{CLR_RESET}")
        return
        
    summary = script_config_service.get_config_summary(config)
    lua_code = script_config_service.generate_lua_script(config_id)
    
    draw_box_top("LOADER DETAILS", 60, CLR_BLUE)
    print_row("ID", str(summary['id']), CLR_BOLD, CLR_BLUE)
    print_row("Label", summary['label'], CLR_BLUE, CLR_BLUE)
    print_row("Secret Key", summary['secret_key'], CLR_CYAN, CLR_BLUE)
    print_row("Target Display Name", summary['target_name'] or "None", CLR_GREEN, CLR_BLUE)
    print_row("Target Roblox ID", summary['target_id'] or "None", CLR_GREEN, CLR_BLUE)
    print_row("Delay Step", f"{summary['delay_step']} second(s)", CLR_GRAY, CLR_BLUE)
    print_row("Trade Cycle Delay", f"{summary['trade_cycle_delay']} second(s)", CLR_GRAY, CLR_BLUE)
    print_row("Toggled ON Items", f"{summary['brainrots_enabled']} / {summary['brainrots_total']}", CLR_YELLOW, CLR_BLUE)
    draw_box_bottom(60, CLR_BLUE)
    
    print(f"\n  {CLR_CYAN}>> Loader URL (HttpGet targets this):{CLR_RESET}")
    print(f"     {CLR_BOLD}http://localhost:5000/api/scripts/loader/{config.secret_key}{CLR_RESET}\n")
    
    print(f"  {CLR_CYAN}>> Copy-Paste Executor Loader Code:{CLR_RESET}")
    print(f"{CLR_GRAY}------------------------------------------------------------{CLR_RESET}")
    print(lua_code.strip())
    print(f"{CLR_GRAY}------------------------------------------------------------{CLR_RESET}")


def run_script_config_menu():
    while True:
        clear_screen()
        print_banner()
        draw_box_top("LUA SCRIPT CONFIGURATIONS", 60, CLR_BLUE)
        print_row("1. List Configurations", "View all per-user loader setups", CLR_RESET, CLR_BLUE)
        print_row("2. Create New Config", "Generate key with custom delays", CLR_RESET, CLR_BLUE)
        print_row("3. Edit Config Target", "Bind target Roblox username", CLR_RESET, CLR_BLUE)
        print_row("4. Toggle Brainrots", "Enable/disable specific items", CLR_RESET, CLR_BLUE)
        print_row("5. Rotate Secret Key", "Rotate config secret_key", CLR_RESET, CLR_BLUE)
        print_row("6. View Loader Details", "Show config details & Lua loader", CLR_RESET, CLR_BLUE)
        print_row("7. Back to Main Menu", "Return to main console matrix", CLR_RESET, CLR_BLUE)
        draw_box_bottom(60, CLR_BLUE)
        
        choice = prompt_input("Select script operation (1-7)", None, 60)
        if choice == "1":
            clear_screen()
            print_banner()
            list_script_configs()
            prompt_input("Press Enter to return", "", 60)
        elif choice == "2":
            clear_screen()
            print_banner()
            create_script_config_interactive()
            prompt_input("Press Enter to return", "", 60)
        elif choice == "3":
            clear_screen()
            print_banner()
            edit_config_target_interactive()
            prompt_input("Press Enter to return", "", 60)
        elif choice == "4":
            clear_screen()
            print_banner()
            toggle_brainrots_interactive()
            prompt_input("Press Enter to return", "", 60)
        elif choice == "5":
            clear_screen()
            print_banner()
            rotate_config_key_interactive()
            prompt_input("Press Enter to return", "", 60)
        elif choice == "6":
            clear_screen()
            print_banner()
            view_loader_details_interactive()
            prompt_input("Press Enter to return", "", 60)
        elif choice == "7" or not choice:
            break


def run_menu():
    while True:
        clear_screen()
        print_banner()
        
        draw_box_top("MAIN COMMAND MATRIX", 60, CLR_BLUE)
        print_row("1. Metrics", "View dashboard & health statistics", CLR_RESET, CLR_BLUE)
        print_row("2. Registry", "Manage license database", CLR_RESET, CLR_BLUE)
        print_row("3. Users", "List database player binds", CLR_RESET, CLR_BLUE)
        print_row("4. Auditing", "Show system activity logs", CLR_RESET, CLR_BLUE)
        print_row("5. Webhook Setup", "Configure Discord Webhook Integration", CLR_RESET, CLR_BLUE)
        print_row("6. Roblox Recon", "Search Roblox player by username", CLR_RESET, CLR_BLUE)
        print_row("7. Inventory", "Monitor brainrot inventory data", CLR_RESET, CLR_BLUE)
        print_row("8. Script Configs", "Manage loader configurations & toggles", CLR_RESET, CLR_BLUE)
        print_row("9. Verification", "Launch Simulated Member portal", CLR_RESET, CLR_BLUE)
        print_row("10. Exit", "Terminate administration console", CLR_RESET, CLR_BLUE)
        draw_box_bottom(60, CLR_BLUE)
        
        try:
            choice = prompt_input("Select operation (1-10)", None, 60)
            if choice == "1":
                clear_screen()
                print_banner()
                get_db_stats()
                prompt_input("Press Enter to return", "", 60)
            elif choice == "2":
                while True:
                    clear_screen()
                    print_banner()
                    draw_box_top("LICENSE REGISTRY OPERATIONS", 60, CLR_CYAN)
                    print_row("1. List All Licenses", "Display current database keys", CLR_RESET, CLR_CYAN)
                    print_row("2. Generate New Keys", "Create custom access licenses", CLR_RESET, CLR_CYAN)
                    print_row("3. Revoke Access Key", "Revoke a license by Key ID", CLR_RESET, CLR_CYAN)
                    print_row("4. Ban Access Key", "Ban a license and bind HWID", CLR_RESET, CLR_CYAN)
                    print_row("5. Back to Main Menu", "Return to main matrix", CLR_RESET, CLR_CYAN)
                    draw_box_bottom(60, CLR_CYAN)
                    
                    reg_choice = prompt_input("Select registry action (1-5)", None, 60)
                    if reg_choice == "1":
                        clear_screen()
                        print_banner()
                        list_keys()
                        prompt_input("Press Enter to return", "", 60)
                    elif reg_choice == "2":
                        clear_screen()
                        print_banner()
                        generate_keys_interactive()
                        prompt_input("Press Enter to return", "", 60)
                    elif reg_choice == "3":
                        clear_screen()
                        print_banner()
                        list_keys()
                        key_id_str = prompt_input("Enter Key ID to revoke", None, 60)
                        if key_id_str.isdigit():
                            perform_revoke(int(key_id_str))
                        else:
                            print(f"\n  {CLR_RED}[x] Invalid Key ID format.{CLR_RESET}")
                        prompt_input("Press Enter to return", "", 60)
                    elif reg_choice == "4":
                        clear_screen()
                        print_banner()
                        list_keys()
                        key_id_str = prompt_input("Enter Key ID to ban", None, 60)
                        if key_id_str.isdigit():
                            perform_ban(int(key_id_str))
                        else:
                            print(f"\n  {CLR_RED}[x] Invalid Key ID format.{CLR_RESET}")
                        prompt_input("Press Enter to return", "", 60)
                    elif reg_choice == "5" or not reg_choice:
                        break
                    else:
                        print(f"\n  {CLR_RED}[x] Invalid registry selection.{CLR_RESET}")
                        prompt_input("Press Enter to return", "", 60)
            elif choice == "3":
                clear_screen()
                print_banner()
                list_users()
                prompt_input("Press Enter to return", "", 60)
            elif choice == "4":
                clear_screen()
                print_banner()
                list_logs()
                prompt_input("Press Enter to return", "", 60)
            elif choice == "5":
                clear_screen()
                print_banner()
                configure_webhook()
                prompt_input("Press Enter to return", "", 60)
            elif choice == "6":
                clear_screen()
                print_banner()
                roblox_lookup()
                prompt_input("Press Enter to return", "", 60)
            elif choice == "7":
                clear_screen()
                print_banner()
                inventory_monitor()
                prompt_input("Press Enter to return", "", 60)
            elif choice == "8":
                run_script_config_menu()
            elif choice == "9":
                clear_screen()
                print_banner()
                member_portal()
                prompt_input("Press Enter to return", "", 60)
            elif choice == "10":
                print(f"\n  {CLR_CYAN}Connection terminated. Goodbye.{CLR_RESET}")
                break
            else:
                print(f"\n  {CLR_RED}[x] Invalid selection index.{CLR_RESET}")
                prompt_input("Press Enter to return", "", 60)
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {CLR_CYAN}Connection terminated. Goodbye.{CLR_RESET}")
            break

def main():
    parser = argparse.ArgumentParser(description="Steal-a-Brainrot CLI Command Console")
    subparsers = parser.add_subparsers(dest="command", help="Available admin commands")

    # Stats
    subparsers.add_parser("stats", help="Show system statistics metrics")

    # Keys
    subparsers.add_parser("keys", help="List all generated license keys")

    # Generate
    gen_parser = subparsers.add_parser("generate", help="Generate new license keys")
    gen_parser.add_argument("--count", type=int, default=1, help="Number of keys to generate")
    gen_parser.add_argument("--days", type=int, default=30, help="Duration of keys in days")
    gen_parser.add_argument("--note", type=str, default="CLI Generated", help="Admin note")

    # Revoke
    rev_parser = subparsers.add_parser("revoke", help="Revoke a key by ID")
    rev_parser.add_argument("id", type=int, help="Key ID to revoke")

    # Ban Key
    ban_parser = subparsers.add_parser("ban", help="Ban a key and its user by ID")
    ban_parser.add_argument("id", type=int, help="Key ID to ban")

    # Users
    subparsers.add_parser("users", help="List all registered Roblox players")

    # Logs
    log_parser = subparsers.add_parser("logs", help="Display recent system activity logs")
    log_parser.add_argument("--limit", type=int, default=20, help="Number of log rows to output")

    # Member Validation Simulator
    subparsers.add_parser("validate-client", help="Simulate a member validating a license key")

    # Webhook Setup
    web_parser = subparsers.add_parser("webhook", help="Configure or view Discord webhook URL")
    web_parser.add_argument("--url", type=str, default=None, help="New Discord Webhook URL to configure")

    # Roblox Lookup
    lookup_parser = subparsers.add_parser("lookup", help="Search a Roblox player by username")
    lookup_parser.add_argument("username", type=str, help="Roblox username to search")

    # Inventory Check
    inv_parser = subparsers.add_parser("inventory", help="Check a player's brainrot inventory")
    inv_parser.add_argument("player_id", type=str, help="Roblox player ID to check")

    # Config Management
    config_parser = subparsers.add_parser("config", help="Manage per-user script configurations")
    config_subparsers = config_parser.add_subparsers(dest="config_command", help="Config operations")
    
    config_subparsers.add_parser("list", help="List all configurations")
    
    cc_parser = config_subparsers.add_parser("create", help="Create a configuration")
    cc_parser.add_argument("--label", type=str, required=True, help="Label for config")
    cc_parser.add_argument("--target", type=str, default=None, help="Target Roblox username")
    cc_parser.add_argument("--delay", type=int, default=1, help="Delay step in seconds")
    cc_parser.add_argument("--trade", type=int, default=2, help="Trade cycle delay in seconds")
    
    ct_parser = config_subparsers.add_parser("target", help="Set target Roblox username for a config")
    ct_parser.add_argument("config_id", type=int, help="Config ID")
    ct_parser.add_argument("username", type=str, help="Target Roblox username")
    
    cg_parser = config_subparsers.add_parser("toggle", help="Toggle a brainrot item status")
    cg_parser.add_argument("config_id", type=int, help="Config ID")
    cg_parser.add_argument("item", type=str, help="Brainrot item name")
    cg_parser.add_argument("enabled", type=int, choices=[0, 1], help="1 for enabled, 0 for disabled")
    
    cga_parser = config_subparsers.add_parser("toggle-all", help="Toggle all brainrot items status")
    cga_parser.add_argument("config_id", type=int, help="Config ID")
    cga_parser.add_argument("enabled", type=int, choices=[0, 1], help="1 for enabled, 0 for disabled")
    
    cat_parser = config_subparsers.add_parser("toggle-category", help="Toggle a brainrot category (OG / SECRET / ANTOH) status")
    cat_parser.add_argument("config_id", type=int, help="Config ID")
    cat_parser.add_argument("category", type=str, choices=["og", "secret", "antoh", "OG", "SECRET", "ANTOH"], help="Category name")
    cat_parser.add_argument("enabled", type=int, choices=[0, 1], help="1 for enabled, 0 for disabled")
    
    cr_parser = config_subparsers.add_parser("rotate", help="Rotate secret key for a config")
    cr_parser.add_argument("config_id", type=int, help="Config ID")
    
    cv_parser = config_subparsers.add_parser("view", help="View loader details and script")
    cv_parser.add_argument("config_id", type=int, help="Config ID")

    args = parser.parse_args()

    # Load Flask application context
    app = create_app()
    with app.app_context():
        if args.command == "stats":
            print_banner()
            get_db_stats()
        elif args.command == "keys":
            print_banner()
            list_keys()
        elif args.command == "generate":
            print_banner()
            generate_new_keys(args.count, args.days, args.note)
        elif args.command == "revoke":
            perform_revoke(args.id)
        elif args.command == "ban":
            perform_ban(args.id)
        elif args.command == "users":
            print_banner()
            list_users()
        elif args.command == "logs":
            print_banner()
            list_logs(args.limit)
        elif args.command == "validate-client":
            print_banner()
            member_portal()
        elif args.command == "webhook":
            if args.url:
                Settings.set('discord_webhook_url', args.url)
                print(f"\n  {CLR_GREEN}[v] Webhook URL updated successfully to: {args.url}{CLR_RESET}")
                # Send test embed
                print(f"  {CLR_CYAN}>> Dispatching test embed to Discord...{CLR_RESET}")
                test_delivered = webhook_service.send_webhook(
                    title="\u2699\ufe0f CLI Webhook Configured",
                    description="The administration command console has successfully updated the webhook receiver URL.",
                    color_hex="8b5cf6",
                    fields=[
                        {"name": "Trigger Source", "value": "SAB CLI Admin Tool (Command Line)", "inline": True},
                        {"name": "Connection Status", "value": "\u2713 Active Connection", "inline": True}
                    ]
                )
                if test_delivered:
                    print(f"  {CLR_GREEN}[v] Test embed delivered successfully to Discord!{CLR_RESET}")
                else:
                    print(f"  {CLR_RED}[x] Failed to deliver test embed. Verify webhook URL is valid.{CLR_RESET}")
            else:
                print_banner()
                configure_webhook()
        elif args.command == "lookup":
            print_banner()
            # Direct lookup via API
            try:
                import requests as http_requests
                r = http_requests.get('http://localhost:5000/api/roblox/search-username', params={'username': args.username}, timeout=15)
                if r.status_code == 200:
                    import json
                    print(json.dumps(r.json(), indent=2))
                else:
                    print(f"  {CLR_RED}[x] {r.json().get('message', 'Error')}{CLR_RESET}")
            except Exception as e:
                print(f"  {CLR_RED}[x] Error: {e}{CLR_RESET}")
        elif args.command == "config":
            if args.config_command == "list":
                print_banner()
                list_script_configs()
            elif args.config_command == "create":
                print_banner()
                try:
                    config = script_config_service.create_config(
                        label=args.label,
                        target_username=args.target,
                        delay_step=args.delay,
                        trade_cycle_delay=args.trade
                    )
                    print(f"  {CLR_GREEN}[v] Config created successfully!{CLR_RESET}")
                    print(f"      ID: {config.id}")
                    print(f"      Secret Key: {config.secret_key}")
                    print(f"      Loader URL: http://localhost:5000/api/scripts/loader/{config.secret_key}")
                except Exception as e:
                    print(f"  {CLR_RED}[x] Error: {e}{CLR_RESET}")
            elif args.config_command == "target":
                config, msg = script_config_service.set_target(args.config_id, args.username)
                if config:
                    print(f"  {CLR_GREEN}[v] {msg}{CLR_RESET}")
                else:
                    print(f"  {CLR_RED}[x] {msg}{CLR_RESET}")
            elif args.config_command == "toggle":
                from app.services.brainrot_catalog import is_valid_brainrot
                if not is_valid_brainrot(args.item):
                    print(f"  {CLR_RED}[x] Error: '{args.item}' is not in the master brainrot catalog.{CLR_RESET}")
                else:
                    config, msg = script_config_service.toggle_brainrot(args.config_id, args.item, bool(args.enabled))
                    if config:
                        print(f"  {CLR_GREEN}[v] {msg}{CLR_RESET}")
                    else:
                        print(f"  {CLR_RED}[x] {msg}{CLR_RESET}")
            elif args.config_command == "toggle-all":
                config, msg = script_config_service.bulk_toggle(args.config_id, bool(args.enabled))
                if config:
                    print(f"  {CLR_GREEN}[v] {msg}{CLR_RESET}")
                else:
                    print(f"  {CLR_RED}[x] {msg}{CLR_RESET}")
            elif args.config_command == "toggle-category":
                config, msg = script_config_service.toggle_category(args.config_id, args.category, bool(args.enabled))
                if config:
                    print(f"  {CLR_GREEN}[v] {msg}{CLR_RESET}")
                else:
                    print(f"  {CLR_RED}[x] {msg}{CLR_RESET}")
            elif args.config_command == "rotate":
                config, msg = script_config_service.update_secret_key(args.config_id)
                if config:
                    print(f"  {CLR_GREEN}[v] {msg}{CLR_RESET}")
                else:
                    print(f"  {CLR_RED}[x] {msg}{CLR_RESET}")
            elif args.config_command == "view":
                print_banner()
                view_loader_details_interactive_by_id(args.config_id)
            else:
                print(f"  {CLR_RED}[x] Please specify a config operation. See --help for details.{CLR_RESET}")
        elif args.command == "inventory":
            print_banner()
            # Direct inventory check
            try:
                import requests as http_requests
                r = http_requests.get('http://localhost:5000/api/roblox/inventory/check', params={'player_id': args.player_id}, timeout=10)
                if r.status_code == 200:
                    import json
                    data = r.json()
                    pct = data.get('completion_pct', 0)
                    filled = int(pct / 5)
                    bar = '#' * filled + '-' * (20 - filled)
                    draw_box_top("COLLECTION STATUS", 60, CLR_GREEN)
                    print_row("Player", data.get('player_name', 'Unknown'), CLR_BOLD, CLR_GREEN)
                    print_row("Owned", f"{data.get('count_owned', 0)}/{data.get('total', 0)}", CLR_BLUE, CLR_GREEN)
                    print_row("Missing", str(data.get('count_missing', 0)), CLR_RED, CLR_GREEN)
                    print_row("Completion", f"[{bar}] {pct}%", CLR_YELLOW, CLR_GREEN)
                    draw_box_bottom(60, CLR_GREEN)
                else:
                    print(f"  {CLR_YELLOW}[!] {r.json().get('message', 'No data')}{CLR_RESET}")
            except Exception as e:
                print(f"  {CLR_RED}[x] Error: {e}{CLR_RESET}")
        else:
            run_menu()

if __name__ == "__main__":
    main()
