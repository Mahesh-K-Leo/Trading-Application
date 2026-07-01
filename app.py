import os
from flask import Flask, render_template, session, redirect, url_for, request
from functools import wraps
from flask_cors import CORS
from dotenv import load_dotenv
from database import init_db
from routes.auth import auth_bp
from routes.market import market_bp
from routes.trade import trade_bp
from routes.funds import funds_bp
from routes.settings import settings_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'kite_paper_trade_secret_2024_xK9mP')
CORS(app)

app.register_blueprint(auth_bp)
app.register_blueprint(market_bp)
app.register_blueprint(trade_bp)
app.register_blueprint(funds_bp)
app.register_blueprint(settings_bp)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username'), theme=session.get('theme','light'))

@app.route('/market')
@login_required
def market():
    return render_template('market.html', username=session.get('username'), theme=session.get('theme','light'))

@app.route('/trade')
@login_required
def trade():
    symbol = request.args.get('symbol', '')
    return render_template('trade.html', username=session.get('username'), theme=session.get('theme','light'), symbol=symbol)

@app.route('/chart')
@login_required
def chart():
    symbol = request.args.get('symbol', 'RELIANCE')
    return render_template('chart.html', username=session.get('username'), theme=session.get('theme','light'), symbol=symbol)

@app.route('/funds')
@login_required
def funds():
    return render_template('funds.html', username=session.get('username'), theme=session.get('theme','light'))

@app.route('/orders')
@login_required
def orders():
    return render_template('orders.html', username=session.get('username'), theme=session.get('theme','light'))

@app.route('/calculator')
@login_required
def calculator():
    return render_template('calculator.html', username=session.get('username'), theme=session.get('theme','light'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', username=session.get('username'), theme=session.get('theme','light'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
