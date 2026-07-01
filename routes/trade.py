from flask import Blueprint, request, session, jsonify
from database import get_db
import yfinance as yf
from datetime import datetime
from functools import wraps

trade_bp = Blueprint('trade', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@trade_bp.route('/api/place-order', methods=['POST'])
@login_required
def place_order():
    user_id = session['user_id']
    data = request.get_json()
    
    symbol = data.get('symbol', '').strip().upper()
    quantity = int(data.get('quantity', 0))
    price = float(data.get('price', 0))
    order_type = data.get('order_type', 'MARKET')
    product_type = data.get('product_type', 'CNC')
    side = data.get('side', 'BUY')
    
    if not symbol or quantity <= 0 or price <= 0:
        return jsonify({'success': False, 'message': 'Invalid order parameters'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT balance FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        current_balance = user[0] if user else 0
        
        total_amount = quantity * price
        
        if product_type == 'CNC':
            brokerage = 0
            stt = (quantity * price * 0.001) if side == 'SELL' else (quantity * price * 0.001)
            exchange = quantity * price * 0.0000335
            stamp_duty = quantity * price * 0.00015 if side == 'BUY' else 0
        else:
            brokerage = min(quantity * price * 0.0003, 20)
            stt = quantity * price * 0.00025 if side == 'SELL' else 0
            exchange = quantity * price * 0.0000335
            stamp_duty = quantity * price * 0.00003 if side == 'BUY' else 0
        
        sebi = 10 / 10000000
        gst = (brokerage + exchange) * 0.18
        
        total_charges = brokerage + stt + exchange + gst + sebi + stamp_duty
        
        if side == 'BUY':
            required_amount = total_amount + total_charges
            if current_balance < required_amount:
                cursor.close()
                return jsonify({'success': False, 'message': 'Insufficient balance'}), 400
        
        cursor.execute('''
            INSERT INTO orders (user_id, symbol, quantity, price, order_type, product_type, side, status, brokerage, total_charges, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'COMPLETED', %s, %s, NOW())
        ''', (user_id, symbol, quantity, price, order_type, product_type, side, brokerage, total_charges))
        
        if side == 'BUY':
            new_balance = current_balance - (total_amount + total_charges)
        else:
            new_balance = current_balance + (total_amount - total_charges)
        
        cursor.execute('UPDATE users SET balance = %s WHERE id = %s', (new_balance, user_id))
        
        cursor.execute('SELECT quantity FROM holdings WHERE user_id = %s AND symbol = %s', (user_id, symbol))
        holding = cursor.fetchone()
        
        if side == 'BUY':
            if holding:
                new_qty = holding[0] + quantity
                cursor.execute('UPDATE holdings SET quantity = %s WHERE user_id = %s AND symbol = %s', 
                             (new_qty, user_id, symbol))
            else:
                cursor.execute('INSERT INTO holdings (user_id, symbol, quantity) VALUES (%s, %s, %s)',
                             (user_id, symbol, quantity))
        else:
            if holding and holding[0] >= quantity:
                new_qty = holding[0] - quantity
                if new_qty == 0:
                    cursor.execute('DELETE FROM holdings WHERE user_id = %s AND symbol = %s', (user_id, symbol))
                else:
                    cursor.execute('UPDATE holdings SET quantity = %s WHERE user_id = %s AND symbol = %s',
                                 (new_qty, user_id, symbol))
        
        conn.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': f'Order placed successfully',
            'new_balance': new_balance,
            'charges': total_charges
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@trade_bp.route('/api/holdings', methods=['GET'])
@login_required
def get_holdings():
    user_id = session['user_id']
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT symbol, quantity FROM holdings WHERE user_id = %s', (user_id,))
        holdings = cursor.fetchall()
        
        holdings_list = []
        for symbol, qty in holdings:
            try:
                ticker = yf.Ticker(f'{symbol}.NS')
                data = ticker.history(period='1d')
                if not data.empty:
                    price = float(data['Close'].iloc[-1])
                    holdings_list.append({
                        'symbol': symbol,
                        'quantity': qty,
                        'price': price,
                        'value': qty * price
                    })
            except:
                pass
        
        cursor.close()
        return jsonify({'success': True, 'holdings': holdings_list})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@trade_bp.route('/api/portfolio', methods=['GET'])
@login_required
def get_portfolio():
    user_id = session['user_id']
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT balance FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        balance = user[0] if user else 0
        
        cursor.execute('SELECT symbol, quantity FROM holdings WHERE user_id = %s', (user_id,))
        holdings = cursor.fetchall()
        
        total_invested = 0
        holdings_list = []
        
        for symbol, qty in holdings:
            try:
                ticker = yf.Ticker(f'{symbol}.NS')
                data = ticker.history(period='1d')
                if not data.empty:
                    price = float(data['Close'].iloc[-1])
                    value = qty * price
                    total_invested += value
                    holdings_list.append({
                        'symbol': symbol,
                        'quantity': qty,
                        'price': price,
                        'value': value
                    })
            except:
                pass
        
        cursor.close()
        
        total_portfolio_value = balance + total_invested
        
        return jsonify({
            'success': True,
            'balance': balance,
            'invested': total_invested,
            'total_value': total_portfolio_value,
            'holdings': holdings_list
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
