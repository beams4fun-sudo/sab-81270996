from flask import Flask, jsonify
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_apscheduler import APScheduler
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from app.config import Config
from app.models import db, AdminUser

# Extensions
login_manager = LoginManager()
socketio = SocketIO(async_mode='threading')
scheduler = APScheduler()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    
    # Initialize SocketIO with cors
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Enable CORS for APIs
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Enable CSRF Protection
    csrf.init_app(app)


    # Blueprints
    from app.routes.auth import auth
    from app.routes.admin import admin
    from app.routes.api import api
    from app.routes.member import member
    from app.routes.roblox_api import roblox_api

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(member, url_prefix='/member')
    app.register_blueprint(roblox_api, url_prefix='/api/roblox')
    
    # Exempt API blueprints from CSRF
    csrf.exempt(api)
    csrf.exempt(roblox_api)



    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return AdminUser.query.get(int(user_id))

    # Context processors
    @app.after_request
    def after_request(response):
        # Additional API-wide CORS headers (redundancy safeguard)
        if request_path_is_api(app):
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # First request setups
    with app.app_context():
        db.create_all()
        # Migration alterations
        try:
            from sqlalchemy import text
            # Add paste_url
            try:
                db.session.execute(text("ALTER TABLE script_configs ADD COLUMN paste_url VARCHAR(256)"))
                db.session.commit()
            except Exception:
                db.session.rollback()

            # Add obfuscate
            try:
                db.session.execute(text("ALTER TABLE script_configs ADD COLUMN obfuscate BOOLEAN DEFAULT 0"))
                db.session.commit()
            except Exception:
                db.session.rollback()

            # Add loadstring_type
            try:
                db.session.execute(text("ALTER TABLE script_configs ADD COLUMN loadstring_type VARCHAR(20) DEFAULT 'raw'"))
                db.session.commit()
            except Exception:
                db.session.rollback()
        except Exception as e:
            print(f"Migration error: {e}")
        
    # Setup background scheduler jobs
    from app.services.scheduler import init_scheduler
    init_scheduler(app, scheduler)

    return app

def request_path_is_api(app):
    from flask import request
    return request.path.startswith('/api/')
