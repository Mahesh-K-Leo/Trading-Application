from flask import Blueprint, request, session, jsonify, render_template
from database import get_db
import yfinance as yf
from functools import wraps
import json

market_bp = Blueprint('market', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@market_bp.route('/api/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('q', '').strip().upper()
    
    if len(query) < 1:
        return jsonify({'success': False, 'message': 'Query too short'})
    
    try:
        # Popular NSE stocks
        stocks = ['RELIANCE', 'TCS', 'INFY', 'WIPRO', 'HINDUNILVR', 'MARUTI', 'SUNPHARMA', 
                  'BAJAJFINSV', 'SBIN', 'HDFCBANK', 'ICICIBANK', 'AXISBANK', 'KOTAKBANK',
                  'LT', 'ULTRACEMCO', 'ASIANPAINT', 'DMART', 'TITAN', 'BAJAJ-AUTO', 'ADANIPORTS']
        
        results = [s for s in stocks if query in s][:10]
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@market_bp.route('/api/stock/<symbol>', methods=['GET'])
@login_required
def get_stock(symbol):
    try:
        ticker = yf.Ticker(f'{symbol}.NS')
        data = ticker.history(period='1d')
        info = ticker.info
        
        if data.empty:
            return jsonify({'success': False, 'message': 'Stock not found'}), 404
        
        current_price = data['Close'].iloc[-1]
        return jsonify({
            'success': True,
            'symbol': symbol,
            'price': float(current_price),
            'currency': 'INR'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@market_bp.route('/api/chart/<symbol>', methods=['GET'])
@login_required
def get_chart(symbol):
    period = request.args.get('period', '1y')
    
    try:
        ticker = yf.Ticker(f'{symbol}.NS')
        hist = ticker.history(period=period)
        
        if hist.empty:
            return jsonify({'success': False, 'message': 'No data available'}), 404
        
        chart_data = {
            'dates': hist.index.strftime('%Y-%m-%d').tolist(),
            'close': hist['Close'].tolist(),
            'open': hist['Open'].tolist(),
            'high': hist['High'].tolist(),
            'low': hist['Low'].tolist(),
            'volume': hist['Volume'].tolist()
        }
        
        return jsonify({'success': True, 'data': chart_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@market_bp.route('/api/watchlist', methods=['GET', 'POST', 'DELETE'])
@login_required
def watchlist():
    user_id = session['user_id']
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            cursor.execute('SELECT symbol FROM watchlist WHERE user_id = %s', (user_id,))
            items = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return jsonify({'success': True, 'watchlist': items})
        
        elif request.method == 'POST':
            data = request.get_json()
            symbol = data.get('symbol', '').strip().upper()
            
            if not symbol:
                return jsonify({'success': False, 'message': 'Symbol required'}), 400
            
            cursor.execute('SELECT id FROM watchlist WHERE user_id = %s AND symbol = %s', (user_id, symbol))
            if cursor.fetchone():
                cursor.close()
                return jsonify({'success': False, 'message': 'Already in watchlist'}), 409
            
            cursor.execute('INSERT INTO watchlist (user_id, symbol) VALUES (%s, %s)', (user_id, symbol))
            conn.commit()
            cursor.close()
            return jsonify({'success': True, 'message': 'Added to watchlist'})
        
        elif request.method == 'DELETE':
            data = request.get_json()
            symbol = data.get('symbol', '').strip().upper()
            
            cursor.execute('DELETE FROM watchlist WHERE user_id = %s AND symbol = %s', (user_id, symbol))
            conn.commit()
            cursor.close()
            return jsonify({'success': True, 'message': 'Removed from watchlist'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
