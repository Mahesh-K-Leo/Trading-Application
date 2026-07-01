from flask import Blueprint, request, session, jsonify
from database import get_db
import bcrypt
from functools import wraps

settings_bp = Blueprint('settings', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

@settings_bp.route('/api/user-profile', methods=['GET'])
@login_required
def get_profile():
    user_id = session['user_id']
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, email, balance FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'username': user[0],
            'email': user[1],
            'balance': user[2]
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@settings_bp.route('/api/update-profile', methods=['POST'])
@login_required
def update_profile():
    user_id = session['user_id']
    data = request.get_json()
    
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'success': False, 'message': 'Username required'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET username = %s WHERE id = %s', (username, user_id))
        conn.commit()
        cursor.close()
        
        session['username'] = username
        
        return jsonify({'success': True, 'message': 'Profile updated'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@settings_bp.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    user_id = session['user_id']
    data = request.get_json()
    
    old_password = data.get('old_password', '').strip()
    new_password = data.get('new_password', '').strip()
    
    if not old_password or not new_password:
        return jsonify({'success': False, 'message': 'Both passwords required'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT password FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        if not user or not verify_password(old_password, user[0]):
            cursor.close()
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
        
        hashed_pw = hash_password(new_password)
        cursor.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_pw, user_id))
        conn.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@settings_bp.route('/api/set-theme', methods=['POST'])
@login_required
def set_theme():
    data = request.get_json()
    theme = data.get('theme', 'light')
    
    if theme not in ['light', 'dark']:
        return jsonify({'success': False, 'message': 'Invalid theme'}), 400
    
    session['theme'] = theme
    return jsonify({'success': True, 'message': 'Theme updated'})

@settings_bp.route('/api/reset-portfolio', methods=['POST'])
@login_required
def reset_portfolio():
    user_id = session['user_id']
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET balance = 1000000 WHERE id = %s', (user_id,))
        cursor.execute('DELETE FROM holdings WHERE user_id = %s', (user_id,))
        cursor.execute('DELETE FROM orders WHERE user_id = %s', (user_id,))
        cursor.execute('DELETE FROM transactions WHERE user_id = %s', (user_id,))
        
        conn.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Portfolio reset successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@settings_bp.route('/api/brokerage-calculator', methods=['POST'])
@login_required
def calculate_brokerage():
    data = request.get_json()
    
    quantity = int(data.get('quantity', 0))
    price = float(data.get('price', 0))
    product_type = data.get('product_type', 'CNC')
    side = data.get('side', 'BUY')
    
    if quantity <= 0 or price <= 0:
        return jsonify({'success': False, 'message': 'Invalid parameters'}), 400
    
    try:
        total_amount = quantity * price
        
        if product_type == 'CNC':
            brokerage = 0
            stt = (total_amount * 0.001) if side == 'SELL' else (total_amount * 0.001)
            exchange = total_amount * 0.0000335
            stamp_duty = total_amount * 0.00015 if side == 'BUY' else 0
        else:
            brokerage = min(total_amount * 0.0003, 20)
            stt = total_amount * 0.00025 if side == 'SELL' else 0
            exchange = total_amount * 0.0000335
            stamp_duty = total_amount * 0.00003 if side == 'BUY' else 0
        
        sebi = 10 / 10000000
        gst = (brokerage + exchange) * 0.18
        
        total_charges = brokerage + stt + exchange + gst + sebi + stamp_duty
        total_with_charges = total_amount + total_charges if side == 'BUY' else total_amount - total_charges
        
        return jsonify({
            'success': True,
            'quantity': quantity,
            'price': price,
            'value': total_amount,
            'brokerage': round(brokerage, 2),
            'stt': round(stt, 2),
            'exchange': round(exchange, 2),
            'stamp_duty': round(stamp_duty, 2),
            'gst': round(gst, 2),
            'sebi': round(sebi, 2),
            'total_charges': round(total_charges, 2),
            'total': round(total_with_charges, 2)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
