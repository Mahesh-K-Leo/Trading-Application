from flask import Blueprint, request, jsonify, session
from database import get_db
from routes.market import get_live_price

trade_bp = Blueprint('trade', __name__)

def calc_charges(order_type, product_type, price, quantity):
    turnover = price * quantity
    brokerage = 0.0
    if product_type == 'MIS':
        brokerage = min(20.0, turnover * 0.0003)
    stt = turnover * 0.001 if product_type == 'CNC' else turnover * 0.00025
    exchange_charges = turnover * 0.0000335
    gst = (brokerage + exchange_charges) * 0.18
    sebi = turnover * 0.000001
    stamp = turnover * 0.00015 if product_type == 'CNC' else turnover * 0.00003
    total = brokerage + stt + exchange_charges + gst + sebi + stamp
    return round(brokerage, 2), round(total, 2)

@trade_bp.route('/api/order/place', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    uid = session['user_id']
    symbol = data.get('symbol', '').upper()
    order_type = data.get('order_type', 'BUY').upper()
    product_type = data.get('product_type', 'CNC').upper()
    price_type = data.get('price_type', 'MARKET').upper()
    quantity = int(data.get('quantity', 0))
    limit_price = float(data.get('limit_price', 0))

    if not symbol or quantity <= 0:
        return jsonify({'error': 'Invalid order details'}), 400

    live = get_live_price(symbol)
    live_price = live.get('price', 0)
    if live_price <= 0:
        return jsonify({'error': 'Could not fetch stock price'}), 400

    if price_type == 'MARKET':
        exec_price = live_price
    else:
        exec_price = limit_price
        if order_type == 'BUY' and live_price > limit_price:
            return jsonify({'error': f'Limit price ₹{limit_price} is below current price ₹{live_price}. Order not executed.'}), 400
        if order_type == 'SELL' and live_price < limit_price:
            return jsonify({'error': f'Limit price ₹{limit_price} is above current price ₹{live_price}. Order not executed.'}), 400

    brokerage, total_charges = calc_charges(order_type, product_type, exec_price, quantity)
    total_amount = exec_price * quantity

    conn = get_db()
    portfolio = conn.execute('SELECT * FROM portfolio WHERE user_id=?', (uid,)).fetchone()
    if not portfolio:
        conn.close()
        return jsonify({'error': 'Portfolio not found'}), 400

    if order_type == 'BUY':
        required = total_amount + total_charges
        if portfolio['available_funds'] < required:
            conn.close()
            return jsonify({'error': f'Insufficient funds. Required ₹{required:,.2f}, Available ₹{portfolio["available_funds"]:,.2f}'}), 400

        existing = conn.execute(
            'SELECT * FROM holdings WHERE user_id=? AND symbol=? AND product_type=?',
            (uid, symbol, product_type)
        ).fetchone()

        if existing:
            new_qty = existing['quantity'] + quantity
            new_avg = ((existing['avg_buy_price'] * existing['quantity']) + (exec_price * quantity)) / new_qty
            conn.execute(
                'UPDATE holdings SET quantity=?, avg_buy_price=? WHERE id=?',
                (new_qty, round(new_avg, 2), existing['id'])
            )
        else:
            conn.execute(
                'INSERT INTO holdings (user_id, symbol, company_name, quantity, avg_buy_price, product_type) VALUES (?,?,?,?,?,?)',
                (uid, symbol, live.get('company_name', symbol), quantity, round(exec_price, 2), product_type)
            )

        new_funds = portfolio['available_funds'] - required
        new_invested = portfolio['total_invested'] + total_amount
        conn.execute('UPDATE portfolio SET available_funds=?, total_invested=? WHERE user_id=?',
                     (new_funds, new_invested, uid))
        conn.execute(
            'INSERT INTO fund_transactions (user_id, type, amount, description, balance_after) VALUES (?,?,?,?,?)',
            (uid, 'DEBIT', required, f'BUY {quantity} x {symbol} @ ₹{exec_price}', new_funds)
        )

    else:  # SELL
        holding = conn.execute(
            'SELECT * FROM holdings WHERE user_id=? AND symbol=? AND product_type=?',
            (uid, symbol, product_type)
        ).fetchone()
        if not holding:
            conn.close()
            return jsonify({'error': f'You do not hold {symbol} ({product_type})'}), 400
        if holding['quantity'] < quantity:
            conn.close()
            return jsonify({'error': f'Insufficient quantity. You hold {holding["quantity"]} shares'}), 400

        new_qty = holding['quantity'] - quantity
        if new_qty == 0:
            conn.execute('DELETE FROM holdings WHERE id=?', (holding['id'],))
        else:
            conn.execute('UPDATE holdings SET quantity=? WHERE id=?', (new_qty, holding['id']))

        proceeds = total_amount - total_charges
        new_funds = portfolio['available_funds'] + proceeds
        cost_basis = holding['avg_buy_price'] * quantity
        new_invested = max(0, portfolio['total_invested'] - cost_basis)
        conn.execute('UPDATE portfolio SET available_funds=?, total_invested=? WHERE user_id=?',
                     (new_funds, new_invested, uid))
        conn.execute(
            'INSERT INTO fund_transactions (user_id, type, amount, description, balance_after) VALUES (?,?,?,?,?)',
            (uid, 'CREDIT', proceeds, f'SELL {quantity} x {symbol} @ ₹{exec_price}', new_funds)
        )

    order = conn.execute(
        '''INSERT INTO orders (user_id, symbol, company_name, order_type, product_type, price_type,
           quantity, price, status, brokerage, total_charges, total_amount)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
        (uid, symbol, live.get('company_name', symbol), order_type, product_type, price_type,
         quantity, round(exec_price, 2), 'EXECUTED', brokerage, total_charges, total_amount)
    )
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': f'Order executed: {order_type} {quantity} x {symbol} @ ₹{exec_price:,.2f}',
        'order_id': order.lastrowid,
        'price': exec_price,
        'total_amount': total_amount,
        'total_charges': total_charges
    })

@trade_bp.route('/api/orders')
def get_orders():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    orders = conn.execute(
        'SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 100',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return jsonify([dict(o) for o in orders])

@trade_bp.route('/api/holdings')
def get_holdings():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    holdings = conn.execute(
        'SELECT * FROM holdings WHERE user_id=? AND quantity > 0',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    result = []
    for h in holdings:
        live = get_live_price(h['symbol'])
        ltp = live.get('price', h['avg_buy_price'])
        invested = h['avg_buy_price'] * h['quantity']
        current = ltp * h['quantity']
        pnl = current - invested
        pnl_pct = (pnl / invested * 100) if invested else 0
        result.append({
            **dict(h),
            'ltp': ltp,
            'invested_amount': round(invested, 2),
            'current_value': round(current, 2),
            'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2),
            'change': live.get('change', 0),
            'change_pct': live.get('change_pct', 0)
        })
    return jsonify(result)

@trade_bp.route('/api/portfolio')
def get_portfolio():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    portfolio = conn.execute('SELECT * FROM portfolio WHERE user_id=?', (session['user_id'],)).fetchone()
    conn.close()
    if not portfolio:
        return jsonify({})
    p = dict(portfolio)
    holdings_resp = get_holdings()
    holdings_data = holdings_resp.get_json()
    total_current = sum(h['current_value'] for h in holdings_data)
    total_invested = sum(h['invested_amount'] for h in holdings_data)
    total_pnl = total_current - total_invested
    p['current_value'] = round(total_current, 2)
    p['total_invested'] = round(total_invested, 2)
    p['total_pnl'] = round(total_pnl, 2)
    p['total_value'] = round(p['available_funds'] + total_current, 2)
    return jsonify(p)
