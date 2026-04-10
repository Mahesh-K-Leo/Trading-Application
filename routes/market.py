from flask import Blueprint, jsonify, session, request
import yfinance as yf
from database import get_db
from nsepython import nseCorporates

market_bp = Blueprint('market', __name__)

# Global cache for NSE stocks
_NSE_STOCKS_CACHE = None

def get_all_nse_stocks():
    """Fetch all NSE stocks dynamically"""
    global _NSE_STOCKS_CACHE
    
    if _NSE_STOCKS_CACHE is not None:
        return _NSE_STOCKS_CACHE
    
    try:
        # Fetch all stocks from NSE
        stocks_list = nseCorporates()
        NSE_STOCKS = {}
        if isinstance(stocks_list, dict):
            for item in stocks_list.values():
                if isinstance(item, dict):
                    symbol = item.get('symbol', '')
                    name = item.get('company', '')
                    if symbol and name:
                        NSE_STOCKS[symbol] = name
        _NSE_STOCKS_CACHE = NSE_STOCKS
        return NSE_STOCKS
    except Exception as e:
        print(f"Error fetching NSE stocks: {e}")
        # Fallback to a basic list if API fails
        return _get_fallback_stocks()

def _get_fallback_stocks():
    """Fallback stock list in case API fails"""
    return {
        "RELIANCE": "Reliance Industries", "TCS": "Tata Consultancy Services",
        "HDFCBANK": "HDFC Bank", "INFY": "Infosys", "ICICIBANK": "ICICI Bank",
        "HINDUNILVR": "Hindustan Unilever", "SBIN": "State Bank of India",
        "BAJFINANCE": "Bajaj Finance", "BHARTIARTL": "Bharti Airtel",
        "KOTAKBANK": "Kotak Mahindra Bank", "WIPRO": "Wipro", "LT": "Larsen & Toubro",
        "HCLTECH": "HCL Technologies", "ASIANPAINT": "Asian Paints",
        "AXISBANK": "Axis Bank", "MARUTI": "Maruti Suzuki", "SUNPHARMA": "Sun Pharmaceutical",
        "TITAN": "Titan Company", "BAJAJFINSV": "Bajaj Finserv",
        "ULTRACEMCO": "UltraTech Cement", "NESTLEIND": "Nestle India",
        "TECHM": "Tech Mahindra", "POWERGRID": "Power Grid Corp",
        "NTPC": "NTPC", "ONGC": "Oil & Natural Gas", "JSWSTEEL": "JSW Steel",
        "TATAMOTORS": "Tata Motors", "ADANIENT": "Adani Enterprises",
        "ADANIPORTS": "Adani Ports", "COALINDIA": "Coal India",
        "DIVISLAB": "Divi's Laboratories", "DRREDDY": "Dr. Reddy's Laboratories"
    }


def get_live_price(symbol):
    try:
        NSE_STOCKS = get_all_nse_stocks()
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.fast_info
        price = getattr(info, 'last_price', None)
        if not price:
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
        prev_close = getattr(info, 'previous_close', None)
        change = 0.0
        change_pct = 0.0
        if price and prev_close:
            change = round(price - prev_close, 2)
            change_pct = round((change / prev_close) * 100, 2)
        return {
            'symbol': symbol,
            'company_name': NSE_STOCKS.get(symbol, symbol),
            'price': round(float(price), 2) if price else 0.0,
            'change': change,
            'change_pct': change_pct,
            'prev_close': round(float(prev_close), 2) if prev_close else 0.0
        }
    except Exception as e:
        NSE_STOCKS = get_all_nse_stocks()
        return {'symbol': symbol, 'company_name': NSE_STOCKS.get(symbol, symbol),
                'price': 0.0, 'change': 0.0, 'change_pct': 0.0, 'prev_close': 0.0}

@market_bp.route('/api/stock/price/<symbol>')
def stock_price(symbol):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(get_live_price(symbol.upper()))

@market_bp.route('/api/stock/search/<query>')
def search_stocks(query):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    q = query.upper()
    NSE_STOCKS = get_all_nse_stocks()
    results = []
    for sym, name in NSE_STOCKS.items():
        if q in sym or q in name.upper():
            results.append({'symbol': sym, 'company_name': name})
        if len(results) >= 20:
            break
    return jsonify(results)

@market_bp.route('/api/stocks/all')
def get_all_stocks():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    NSE_STOCKS = get_all_nse_stocks()
    stocks_list = [{'symbol': sym, 'company_name': name} for sym, name in NSE_STOCKS.items()]
    return jsonify(stocks_list)

@market_bp.route('/api/stock/chart/<symbol>/<period>')
def stock_chart(symbol, period):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    period_map = {'1d': ('1d', '5m'), '5d': ('5d', '15m'),
                  '1mo': ('1mo', '1h'), '3mo': ('3mo', '1d'), '1y': ('1y', '1d')}
    p, interval = period_map.get(period, ('1mo', '1d'))
    try:
        ticker = yf.Ticker(f"{symbol.upper()}.NS")
        hist = ticker.history(period=p, interval=interval)
        if hist.empty:
            return jsonify([])
        data = []
        for ts, row in hist.iterrows():
            t = int(ts.timestamp())
            data.append({
                'time': t,
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume'])
            })
        return jsonify(data)
    except Exception as e:
        return jsonify([])

@market_bp.route('/api/watchlist')
def get_watchlist():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    items = conn.execute(
        'SELECT symbol, company_name FROM watchlist WHERE user_id=? ORDER BY added_at DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    result = []
    for item in items:
        price_data = get_live_price(item['symbol'])
        result.append({**dict(item), **price_data})
    return jsonify(result)

@market_bp.route('/api/watchlist/add', methods=['POST'])
def add_watchlist():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    symbol = data.get('symbol', '').upper()
    company_name = NSE_STOCKS.get(symbol, symbol)
    conn = get_db()
    try:
        conn.execute(
            'INSERT OR IGNORE INTO watchlist (user_id, symbol, company_name) VALUES (?,?,?)',
            (session['user_id'], symbol, company_name)
        )
        conn.commit()
    except:
        pass
    conn.close()
    return jsonify({'success': True})

@market_bp.route('/api/watchlist/remove/<symbol>', methods=['DELETE'])
def remove_watchlist(symbol):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    conn.execute('DELETE FROM watchlist WHERE user_id=? AND symbol=?',
                 (session['user_id'], symbol.upper()))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@market_bp.route('/api/market/overview')
def market_overview():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    top = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
           'SBIN', 'WIPRO', 'BAJFINANCE', 'HINDUNILVR', 'ADANIENT']
    results = [get_live_price(s) for s in top]
    return jsonify(results)
