from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.models import db, AdminUser, ActivityLog
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    # Check if any admins exist; if not, force redirect to setup
    admin_count = AdminUser.query.count()
    if admin_count == 0:
        return redirect(url_for('auth.setup'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('This admin account has been deactivated.', 'danger')
                return render_template('login.html')
                
            login_user(user)
            user.last_login = datetime.utcnow()
            
            # Log login event
            log = ActivityLog(
                admin_id=user.id,
                event_type='ADMIN_LOGIN',
                details=f"Admin {user.username} logged in from {request.remote_addr}"
            )
            db.session.add(log)
            db.session.commit()
            
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

@auth.route('/logout')
def logout():
    if current_user.is_authenticated:
        log = ActivityLog(
            admin_id=current_user.id,
            event_type='ADMIN_LOGOUT',
            details=f"Admin {current_user.username} logged out"
        )
        db.session.add(log)
        db.session.commit()
        logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/setup', methods=['GET', 'POST'])
def setup():
    # Setup only works if there are zero admin accounts
    admin_count = AdminUser.query.count()
    if admin_count > 0:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('setup.html')
            
        new_admin = AdminUser(
            username=username,
            email=email,
            role='superadmin',
            is_active=True
        )
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        
        # Log first action
        log = ActivityLog(
            admin_id=new_admin.id,
            event_type='SYSTEM_INITIALIZED',
            details="First superadmin created. System setup complete."
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Setup complete! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('setup.html')
