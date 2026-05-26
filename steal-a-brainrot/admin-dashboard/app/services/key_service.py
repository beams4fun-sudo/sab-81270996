import secrets
import hashlib
from datetime import datetime, timedelta
from app.models import db, Key, User, ActivityLog, Settings

def generate_key(duration_days, created_by_id=None, note='', count=1):
    generated_keys = []
    for _ in range(count):
        raw_key = f"SAB-{secrets.token_hex(16).upper()}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_preview = f"SAB-{raw_key[-8:]}"

        new_key = Key(
            key_hash=key_hash,
            key_string=raw_key,
            key_preview=key_preview,
            duration_days=duration_days,
            created_by=created_by_id,
            note=note,
            status='unused'
        )

        db.session.add(new_key)
        
        # We need to temporarily hold the plain text key so the admin can copy it once.
        generated_keys.append(raw_key)
        
    db.session.commit()
    
    # Log event
    log = ActivityLog(
        admin_id=created_by_id,
        event_type='KEY_GENERATED',
        details=f"Generated {count} keys with {duration_days}-day duration."
    )
    db.session.add(log)
    db.session.commit()
    
    return generated_keys

def validate_key(key_string, hwid, ip_address=None, roblox_id=None, roblox_name=None):
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()
    key = Key.query.filter_by(key_hash=key_hash).first()
    
    if not key:
        log_event(None, None, 'VALIDATION_FAILED', ip_address, hwid, f"Invalid key entered: {key_string[:10]}...")
        return {'valid': False, 'message': 'Invalid key format or key does not exist.'}

    if key.status == 'revoked':
        log_event(None, key.id, 'VALIDATION_FAILED', ip_address, hwid, "Attempted to use revoked key.")
        return {'valid': False, 'message': 'Key has been revoked.'}

    if key.status == 'banned':
        log_event(None, key.id, 'VALIDATION_FAILED', ip_address, hwid, "Attempted to use banned key.")
        return {'valid': False, 'message': 'Key has been banned.'}

    if key.status == 'expired' or key.is_expired:
        if key.status != 'expired':
            key.status = 'expired'
            db.session.commit()
        log_event(key.user_id, key.id, 'VALIDATION_FAILED', ip_address, hwid, "Attempted to use expired key.")
        return {'valid': False, 'message': 'Key has expired.'}

    # If key is unused, activate it and bind HWID + User
    if key.status == 'unused':
        # Create or find User
        username = roblox_name or f"Roblox_{roblox_id or 'Unknown'}"
        user = User.query.filter_by(roblox_id=str(roblox_id)).first() if roblox_id else None
        
        if not user:
            user = User(
                username=username,
                roblox_id=str(roblox_id) if roblox_id else None,
                hwid=hwid,
                ip_address=ip_address
            )
            db.session.add(user)
            db.session.commit()
        else:
            user.hwid = hwid
            user.ip_address = ip_address
            db.session.commit()

        key.user_id = user.id
        key.hwid = hwid
        key.activated_at = datetime.utcnow()
        key.expires_at = key.activated_at + timedelta(days=key.duration_days)
        key.status = 'active'
        db.session.commit()
        
        log_event(user.id, key.id, 'KEY_ACTIVATED', ip_address, hwid, f"Key activated for user {username}")
        
        # Dispatch webhook event
        try:
            from app.services import webhook_service
            webhook_service.send_key_activated(username, key.key_preview, hwid)
        except Exception as e:
            print(f"Error dispatching activation webhook: {e}")

        return {
            'valid': True, 
            'message': 'Key activated successfully.', 
            'expires_at': key.expires_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    # If key is active, verify HWID
    if key.status == 'active':
        if key.hwid != hwid:
            log_event(key.user_id, key.id, 'HWID_MISMATCH', ip_address, hwid, f"HWID mismatch. Stored: {key.hwid}, Sent: {hwid}")
            
            # Dispatch suspicious activity webhook event
            try:
                from app.services import webhook_service
                user_name = key.user.username if key.user else "Unknown User"
                webhook_service.send_suspicious_activity(
                    "HWID_MISMATCH",
                    f"User **{user_name}** attempted validation using key preview `{key.key_preview}` with HWID `{hwid}` (Stored HWID: `{key.hwid}`). Access blocked."
                )
            except Exception as e:
                print(f"Error dispatching suspicious activity webhook: {e}")

            return {'valid': False, 'message': 'Key is bound to another device.'}
        
        # Update user info
        if key.user:
            key.user.ip_address = ip_address
            key.user.updated_at = datetime.utcnow()
            db.session.commit()
            
        log_event(key.user_id, key.id, 'KEY_VALIDATED', ip_address, hwid, "Successful validation check.")
        return {
            'valid': True, 
            'message': 'Validation successful.', 
            'expires_at': key.expires_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    return {'valid': False, 'message': 'Unknown key status.'}

def revoke_key(key_id, admin_id=None):
    key = Key.query.get(key_id)
    if key:
        key.status = 'revoked'
        db.session.commit()
        log_event(key.user_id, key.id, 'KEY_REVOKED', None, None, f"Key revoked by admin {admin_id}", admin_id)
        return True
    return False

def ban_key(key_id, admin_id=None):
    key = Key.query.get(key_id)
    if key:
        key.status = 'banned'
        if key.user:
            key.user.status = 'banned'
        db.session.commit()
        log_event(key.user_id, key.id, 'KEY_BANNED', None, None, f"Key and user banned by admin {admin_id}", admin_id)
        return True
    return False

def log_event(user_id, key_id, event_type, ip_address, hwid, details, admin_id=None):
    log = ActivityLog(
        user_id=user_id,
        key_id=key_id,
        admin_id=admin_id,
        event_type=event_type,
        ip_address=ip_address,
        hwid=hwid,
        details=details
    )
    db.session.add(log)
    db.session.commit()

def get_stats():
    total_keys = Key.query.count()
    active_keys = Key.query.filter_by(status='active').count()
    expired_keys = Key.query.filter_by(status='expired').count()
    unused_keys = Key.query.filter_by(status='unused').count()
    total_users = User.query.count()
    
    # Events today (UTC)
    today = datetime.utcnow().date()
    events_today = ActivityLog.query.filter(ActivityLog.created_at >= datetime.combine(today, datetime.min.time())).count()
    
    return {
        'total_keys': total_keys,
        'active_keys': active_keys,
        'expired_keys': expired_keys,
        'unused_keys': unused_keys,
        'total_users': total_users,
        'events_today': events_today
    }
