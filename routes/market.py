from flask import Blueprint, jsonify, session, request
import yfinance as yf
from database import get_db

market_bp = Blueprint('market', __name__)

NSE_STOCKS = {
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
    "DIVISLAB": "Divi's Laboratories", "DRREDDY": "Dr. Reddy's Laboratories",
    "EICHERMOT": "Eicher Motors", "GRASIM": "Grasim Industries",
    "HEROMOTOCO": "Hero MotoCorp", "HINDALCO": "Hindalco Industries",
    "INDUSINDBK": "IndusInd Bank", "ITC": "ITC", "M&M": "Mahindra & Mahindra",
    "BRITANNIA": "Britannia Industries", "CIPLA": "Cipla",
    "BAJAJ-AUTO": "Bajaj Auto", "TATACONSUM": "Tata Consumer Products",
    "APOLLOHOSP": "Apollo Hospitals", "BPCL": "Bharat Petroleum",
    "HDFCLIFE": "HDFC Life Insurance", "SBILIFE": "SBI Life Insurance",
    "TATASTEEL": "Tata Steel", "UPL": "UPL", "VEDL": "Vedanta",
    "ZOMATO": "Zomato", "PAYTM": "Paytm", "NYKAA": "Nykaa",
    "IRCTC": "IRCTC", "HAL": "Hindustan Aeronautics",
    "PIDILITIND": "Pidilite Industries", "SIEMENS": "Siemens India",
    "HAVELLS": "Havells India", "DABUR": "Dabur India",
    "MARICO": "Marico", "COLPAL": "Colgate-Palmolive",
    "GODREJCP": "Godrej Consumer Products", "BERGEPAINT": "Berger Paints",
    "ICICIPRULI": "ICICI Prudential", "BANDHANBNK": "Bandhan Bank",
    "IDFCFIRSTB": "IDFC First Bank", "PNB": "Punjab National Bank",
    "BANKBARODA": "Bank of Baroda", "CANBK": "Canara Bank",
    "RECLTD": "REC", "PFC": "Power Finance Corp",
    "TATAPOWER": "Tata Power", "ADANIGREEN": "Adani Green Energy",
    "ADANIPOWER": "Adani Power", "ATGL": "Adani Total Gas",
    "DMART": "Avenue Supermarts", "JUBLFOOD": "Jubilant FoodWorks",
    "MCDOWELL-N": "United Spirits", "UNITDSPR": "United Spirits",
    "OFSS": "Oracle Financial Services", "MPHASIS": "Mphasis",
    "PERSISTENT": "Persistent Systems", "COFORGE": "Coforge",
    "LTIM": "LTIMindtree", "ZYDUSLIFE": "Zydus Lifesciences",
    "TORNTPHARM": "Torrent Pharmaceuticals", "AUROPHARMA": "Aurobindo Pharma",
    "LUPIN": "Lupin", "BIOCON": "Biocon",
    "MOTHERSON": "Samvardhana Motherson", "BALKRISIND": "Balkrishna Industries",
    "EXIDEIND": "Exide Industries", "BOSCHLTD": "Bosch",
    "ASHOKLEY": "Ashok Leyland", "TVSMOTOR": "TVS Motor",
    "MRF": "MRF", "CUMMINSIND": "Cummins India",
    "WHIRLPOOL": "Whirlpool India", "VOLTAS": "Voltas",
    "BLUEDART": "Blue Dart Express", "INDIGO": "IndiGo"
}


def get_live_price(symbol):
    try:
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
    results = []
    for sym, name in NSE_STOCKS.items():
        if q in sym or q in name.upper():
            results.append({'symbol': sym, 'company_name': name})
        if len(results) >= 10:
            break
    return jsonify(results)

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
