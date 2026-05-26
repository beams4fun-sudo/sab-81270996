from datetime import datetime
from app.models import db, Key
from app.services.webhook_service import send_key_expired

def init_scheduler(app, scheduler):
    scheduler.init_app(app)
    
    # Define periodic job to check for expired keys
    @scheduler.task('interval', id='check_expired_keys', hours=1, misfire_grace_time=900)
    def check_expired_keys():
        with app.app_context():
            now = datetime.utcnow()
            expired_keys = Key.query.filter(
                Key.status == 'active',
                Key.expires_at < now
            ).all()
            
            for key in expired_keys:
                key.status = 'expired'
                username = key.user.username if key.user else "Unknown"
                send_key_expired(username, key.key_preview)
                
            db.session.commit()
            if expired_keys:
                print(f"[{datetime.now()}] Expired {len(expired_keys)} keys successfully.")

    scheduler.start()
