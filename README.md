# KiteTrade — Indian Paper Trading App

A full-featured Indian stock market paper trading web application built with Python (Flask) + SQLite3 + HTML/CSS/JS. Trade NSE stocks with real-time prices using ₹10,00,000 virtual money.

## Features

- **Real-time NSE stock prices** via Yahoo Finance (yfinance)
- **Buy/Sell orders** — Market & Limit orders, CNC & MIS product types
- **Live candlestick charts** with SMA (20/50/200) and EMA (9/21) indicators
- **Portfolio tracking** — Holdings, P&L, invested value
- **Watchlist** — Add/remove stocks, live price updates
- **Funds management** — Add/withdraw virtual funds, transaction history
- **Order book** — Complete trade history with CSV export
- **Brokerage calculator** — Full charge breakdown (STT, GST, SEBI, Stamp Duty)
- **Settings** — Profile update, password change, theme toggle, portfolio reset
- **Dark/Light theme**

## Setup & Installation

### 1. Clone / Download the project

```bash
cd stock_app
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Configure the database

Create a `.env` file in the project root with your database type and credentials.

For SQLite (no local MySQL server needed):

```env
DB_TYPE=sqlite
SECRET_KEY=your_secret_key
```

For MySQL:

```env
DB_TYPE=mysql
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=stock_app
DB_PORT=3306
SECRET_KEY=your_secret_key
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the app

```bash
python app.py
```

### 6. Open in browser

```
http://localhost:5000
```

### 7. Push to GitHub

```bash
git init
git add .
git commit -m "MySQL migration and GitHub setup"
git branch -M main
git remote add origin https://github.com/yourusername/stock-app.git
git push -u origin main
```

## First Use

1. Go to `http://localhost:5000/register`
2. Create an account
3. You automatically receive **₹10,00,000** virtual funds
4. Search for NSE stocks (e.g. RELIANCE, TCS, INFY)
5. Place buy/sell orders and track your portfolio!

## Project Structure

```
stock_app/
├── app.py                  # Main Flask application
├── database.py             # SQLite3 schema & init
├── requirements.txt
├── routes/
│   ├── auth.py             # Login, Register, Logout
│   ├── market.py           # Stock prices, search, charts, watchlist
│   ├── trade.py            # Order placement, holdings, portfolio
│   ├── funds.py            # Fund management
│   └── settings.py         # Profile, password, theme, reset
├── templates/
│   ├── base.html           # Sidebar layout
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html      # Portfolio overview
│   ├── market.html         # Stock search & watchlist
│   ├── trade.html          # Order form
│   ├── chart.html          # Candlestick charts + indicators
│   ├── funds.html          # Fund management
│   ├── orders.html         # Order book & history
│   ├── calculator.html     # Brokerage calculator
│   └── settings.html       # User settings
└── static/
    ├── css/style.css
    └── js/main.js
```

## Brokerage Model (Zerodha)

| Charge | Delivery (CNC) | Intraday (MIS) |
|--------|---------------|----------------|
| Brokerage | ₹0 | ₹20 or 0.03% (lower) |
| STT | 0.1% both sides | 0.025% sell side |
| Exchange (NSE) | 0.00335% | 0.00335% |
| GST | 18% on brokerage + exchange | same |
| SEBI | ₹10/crore | same |
| Stamp Duty | 0.015% on buy | 0.003% on buy |

## Notes

- All prices fetched from Yahoo Finance (NSE: `.NS` suffix)
- Market hours: Mon–Fri 9:15 AM – 3:30 PM IST
- Prices may be delayed by 15 minutes during off-market hours
- No real money involved — paper trading only
