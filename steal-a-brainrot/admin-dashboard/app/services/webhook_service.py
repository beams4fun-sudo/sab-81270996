from discord_webhook import DiscordWebhook, DiscordEmbed
from app.models import Settings
from datetime import datetime

WEBHOOK_FOOTER = "Steal a Brainrot Logs | #Splikzy"
WEBHOOK_USERNAME = "SAB Logs"

def get_webhook_url():
    return Settings.get('discord_webhook_url')

def send_webhook(title, description, color_hex="3b82f6", fields=None, webhook_url_override=None):
    webhook_url = webhook_url_override or get_webhook_url()
    if not webhook_url:
        return False
        
    try:
        # Convert hex to decimal
        color_dec = int(color_hex.replace("#", ""), 16)
        
        webhook = DiscordWebhook(
            url=webhook_url,
            username=WEBHOOK_USERNAME,
            avatar_url="https://images.rbxcdn.com/f9630fc6e7a2b988f98ec34293f0b2f0.png"
        )
        embed = DiscordEmbed(
            title=title,
            description=description,
            color=color_dec
        )
        embed.set_footer(text=WEBHOOK_FOOTER)
        embed.set_timestamp()

        
        if fields:
            for field in fields:
                embed.add_embed_field(
                    name=field.get('name', ''),
                    value=field.get('value', ''),
                    inline=field.get('inline', True)
                )
                
        webhook.add_embed(embed)
        resp = webhook.execute()
        return True
    except Exception as e:
        print(f"Error sending webhook: {e}")
        return False

def send_key_activated(username, key_preview, hwid):
    send_webhook(
        title="\U0001f511 License Activated",
        description=f"A new license key has been bound and activated.",
        color_hex="10b981", # Green
        fields=[
            {"name": "Roblox Username", "value": username, "inline": True},
            {"name": "Key Preview", "value": key_preview, "inline": True},
            {"name": "HWID", "value": f"`{hwid}`", "inline": False}
        ]
    )

def send_key_expired(username, key_preview):
    send_webhook(
        title="\u231b License Expired",
        description=f"User license has reached its expiration date.",
        color_hex="f59e0b", # Amber
        fields=[
            {"name": "Username", "value": username, "inline": True},
            {"name": "Key", "value": key_preview, "inline": True}
        ]
    )

def send_suspicious_activity(event, details):
    send_webhook(
        title="\U0001f6a8 Alert: Suspicious Activity",
        description=f"An abnormal event was detected by the validation system.",
        color_hex="ef4444", # Red
        fields=[
            {"name": "Event Type", "value": event, "inline": True},
            {"name": "Details", "value": details, "inline": False}
        ]
    )

def send_admin_action(admin_name, action, target):
    send_webhook(
        title="\U0001f6e1\ufe0f Admin Action Logged",
        description=f"An administrator performed an operation on the system.",
        color_hex="8b5cf6", # Purple
        fields=[
            {"name": "Admin", "value": admin_name, "inline": True},
            {"name": "Action", "value": action, "inline": True},
            {"name": "Target", "value": target, "inline": False}
        ]
    )

def send_inventory_update(player_name, player_id, count_owned, total, completion_pct):
    # Progress bar visual
    filled = int(completion_pct / 5)
    bar = "\u2588" * filled + "\u2591" * (20 - filled)

    send_webhook(
        title="\U0001f4e6 Inventory Report Received",
        description=f"In-game inventory data synced for **{player_name}**.",
        color_hex="6366f1", # Indigo
        fields=[
            {"name": "Player", "value": f"[{player_name}](https://www.roblox.com/users/{player_id}/profile)", "inline": True},
            {"name": "Player ID", "value": f"`{player_id}`", "inline": True},
            {"name": "Collection", "value": f"**{count_owned}** / {total} brainrots", "inline": True},
            {"name": "Completion", "value": f"`{bar}` {completion_pct}%", "inline": False}
        ]
    )

def send_player_lookup(player_name, player_id, presence_status, avatar_url=None):
    send_webhook(
        title="\U0001f50d Player Lookup",
        description=f"A Roblox username search was performed.",
        color_hex="0ea5e9", # Sky
        fields=[
            {"name": "Username", "value": f"[{player_name}](https://www.roblox.com/users/{player_id}/profile)", "inline": True},
            {"name": "User ID", "value": f"`{player_id}`", "inline": True},
            {"name": "Status", "value": presence_status or "Unknown", "inline": True}
        ]
    )
