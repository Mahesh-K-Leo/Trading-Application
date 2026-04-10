from flask import Blueprint, request, jsonify, session
from database import get_db

funds_bp = Blueprint('funds', __name__)

@funds_bp.route('/api/funds/add', methods=['POST'])
def add_funds():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    amount = float(data.get('amount', 0))
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    if amount > 500000:
        return jsonify({'error': 'Maximum single deposit is ₹5,00,000'}), 400
    uid = session['user_id']
    conn = get_db()
    portfolio = conn.execute('SELECT * FROM portfolio WHERE user_id=?', (uid,)).fetchone()
    new_balance = portfolio['available_funds'] + amount
    if new_balance > 5000000:
        conn.close()
        return jsonify({'error': 'Total funds cannot exceed ₹50,00,000'}), 400
    conn.execute('UPDATE portfolio SET available_funds=? WHERE user_id=?', (new_balance, uid))
    conn.execute(
        'INSERT INTO fund_transactions (user_id, type, amount, description, balance_after) VALUES (?,?,?,?,?)',
        (uid, 'CREDIT', amount, 'Fund deposit', new_balance)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'new_balance': new_balance})

@funds_bp.route('/api/funds/withdraw', methods=['POST'])
def withdraw_funds():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    amount = float(data.get('amount', 0))
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    uid = session['user_id']
    conn = get_db()
    portfolio = conn.execute('SELECT * FROM portfolio WHERE user_id=?', (uid,)).fetchone()
    if portfolio['available_funds'] < amount:
        conn.close()
        return jsonify({'error': 'Insufficient available funds'}), 400
    new_balance = portfolio['available_funds'] - amount
    conn.execute('UPDATE portfolio SET available_funds=? WHERE user_id=?', (new_balance, uid))
    conn.execute(
        'INSERT INTO fund_transactions (user_id, type, amount, description, balance_after) VALUES (?,?,?,?,?)',
        (uid, 'DEBIT', amount, 'Fund withdrawal', new_balance)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'new_balance': new_balance})

@funds_bp.route('/api/funds/history')
def fund_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    txns = conn.execute(
        'SELECT * FROM fund_transactions WHERE user_id=? ORDER BY created_at DESC LIMIT 100',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return jsonify([dict(t) for t in txns])
