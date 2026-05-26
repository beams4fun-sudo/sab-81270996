from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services import key_service
from app.models import Key

member = Blueprint('member', __name__)

@member.route('/', methods=['GET', 'POST'])
def portal():
    if request.method == 'POST':
        key_string = request.form.get('key', '').strip()
        # Simulated HWID for web browser login (IP based fingerprint or session variable)
        hwid = request.headers.get('User-Agent', 'WebBrowser')
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        if not key_string:
            flash('Please enter your license key.', 'danger')
            return redirect(url_for('member.portal'))

        result = key_service.validate_key(
            key_string=key_string,
            hwid=hwid,
            ip_address=ip,
            roblox_name="Web Member"
        )

        if result.get('valid'):
            session['member_key'] = key_string
            session['member_hwid'] = hwid
            flash('Access Granted!', 'success')
            return redirect(url_for('member.dashboard'))
        else:
            flash(result.get('message', 'Validation failed.'), 'danger')
            return redirect(url_for('member.portal'))

    return render_template('member/portal.html')

@member.route('/dashboard')
def dashboard():
    key_string = session.get('member_key')
    if not key_string:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('member.portal'))

    import hashlib
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()
    key_info = Key.query.filter_by(key_hash=key_hash).first()

    if not key_info or key_info.status not in ['active', 'unused']:
        session.pop('member_key', None)
        flash('Your key has been deactivated or expired.', 'danger')
        return redirect(url_for('member.portal'))

    return render_template('member/dashboard.html', key_info=key_info)

@member.route('/logout')
def logout():
    session.pop('member_key', None)
    session.pop('member_hwid', None)
    return redirect(url_for('member.portal'))
