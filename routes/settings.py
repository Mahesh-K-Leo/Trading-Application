from flask import Blueprint, request, jsonify, session
import bcrypt
from database import get_db

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/api/settings/profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    uid = session['user_id']
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    if not full_name or not email:
        return jsonify({'error': 'Fields required'}), 400
    conn = get_db()
    try:
        conn.execute('UPDATE users SET full_name=?, email=? WHERE id=?', (full_name, email, uid))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except:
        conn.close()
        return jsonify({'error': 'Email already in use'}), 400

@settings_bp.route('/api/settings/password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    if len(new_pw) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    uid = session['user_id']
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    if not bcrypt.checkpw(old_pw.encode(), user['password_hash'].encode()):
        conn.close()
        return jsonify({'error': 'Incorrect current password'}), 400
    new_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
    conn.execute('UPDATE users SET password_hash=? WHERE id=?', (new_hash, uid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@settings_bp.route('/api/settings/theme', methods=['POST'])
def update_theme():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    theme = data.get('theme', 'dark')
    uid = session['user_id']
    conn = get_db()
    conn.execute('UPDATE users SET theme=? WHERE id=?', (theme, uid))
    conn.commit()
    conn.close()
    session['theme'] = theme
    return jsonify({'success': True})

@settings_bp.route('/api/settings/reset-portfolio', methods=['POST'])
def reset_portfolio():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    uid = session['user_id']
    conn = get_db()
    conn.execute('DELETE FROM holdings WHERE user_id=?', (uid,))
    conn.execute('DELETE FROM orders WHERE user_id=?', (uid,))
    conn.execute('DELETE FROM fund_transactions WHERE user_id=?', (uid,))
    conn.execute('UPDATE portfolio SET available_funds=1000000.0, total_invested=0, current_value=0, total_pnl=0 WHERE user_id=?', (uid,))
    conn.execute(
        'INSERT INTO fund_transactions (user_id, type, amount, description, balance_after) VALUES (?,?,?,?,?)',
        (uid, 'CREDIT', 1000000.0, 'Portfolio reset - Starting funds restored', 1000000.0)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@settings_bp.route('/api/settings/user')
def get_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    user = conn.execute('SELECT id, username, email, full_name, theme, created_at FROM users WHERE id=?',
                        (session['user_id'],)).fetchone()
    conn.close()
    return jsonify(dict(user))
