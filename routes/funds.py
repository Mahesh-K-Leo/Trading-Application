from flask import Blueprint, request, session, jsonify
from database import get_db
from datetime import datetime
from functools import wraps

funds_bp = Blueprint('funds', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@funds_bp.route('/api/add-funds', methods=['POST'])
@login_required
def add_funds():
    user_id = session['user_id']
    data = request.get_json()
    
    amount = float(data.get('amount', 0))
    
    if amount <= 0 or amount > 10000000:
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT balance FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        current_balance = user[0] if user else 0
        
        new_balance = current_balance + amount
        cursor.execute('UPDATE users SET balance = %s WHERE id = %s', (new_balance, user_id))
        
        cursor.execute('''
            INSERT INTO transactions (user_id, type, amount, description, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        ''', (user_id, 'DEPOSIT', amount, f'Added ₹{amount}'))
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Funds added successfully',
            'new_balance': new_balance
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@funds_bp.route('/api/withdraw-funds', methods=['POST'])
@login_required
def withdraw_funds():
    user_id = session['user_id']
    data = request.get_json()
    
    amount = float(data.get('amount', 0))
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT balance FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        current_balance = user[0] if user else 0
        
        if current_balance < amount:
            cursor.close()
            return jsonify({'success': False, 'message': 'Insufficient balance'}), 400
        
        new_balance = current_balance - amount
        cursor.execute('UPDATE users SET balance = %s WHERE id = %s', (new_balance, user_id))
        
        cursor.execute('''
            INSERT INTO transactions (user_id, type, amount, description, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        ''', (user_id, 'WITHDRAWAL', amount, f'Withdrawn ₹{amount}'))
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Funds withdrawn successfully',
            'new_balance': new_balance
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@funds_bp.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    user_id = session['user_id']
    limit = request.args.get('limit', 50, type=int)
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT type, amount, description, created_at 
            FROM transactions 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        ''', (user_id, limit))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'type': row[0],
                'amount': row[1],
                'description': row[2],
                'date': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else ''
            })
        
        cursor.close()
        return jsonify({'success': True, 'transactions': transactions})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
