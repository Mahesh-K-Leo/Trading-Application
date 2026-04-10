import os
import re
import sqlite3
from dotenv import load_dotenv
import pymysql

load_dotenv()

DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'stock_app')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_CHARSET = os.getenv('DB_CHARSET', 'utf8mb4')
DB_PATH = os.path.join(os.path.dirname(__file__), 'stock_app.db')


class DatabaseConnection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, query, params=None):
        if params is None:
            params = ()
        query = re.sub(r"\?", "%s", query)
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        self._connection.commit()

    def close(self):
        self._connection.close()

    def cursor(self):
        return self._connection.cursor()

    def rollback(self):
        return self._connection.rollback()


class SqliteConnection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, query, params=None):
        if params is None:
            params = ()
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        self._connection.commit()

    def close(self):
        self._connection.close()

    def cursor(self):
        return self._connection.cursor()

    def rollback(self):
        return self._connection.rollback()


def get_db():
    if DB_TYPE == 'sqlite':
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        return SqliteConnection(conn)

    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        charset=DB_CHARSET,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    return DatabaseConnection(conn)


def ensure_database():
    if DB_TYPE == 'sqlite':
        return

    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        charset=DB_CHARSET,
        cursorclass=pymysql.cursors.DictCursor,
    )
    with conn.cursor() as cursor:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET {DB_CHARSET} COLLATE {DB_CHARSET}_unicode_ci"
        )
    conn.commit()
    conn.close()


def init_db():
    if DB_TYPE == 'sqlite':
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            theme TEXT DEFAULT 'dark',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            available_funds REAL DEFAULT 1000000.0,
            total_invested REAL DEFAULT 0.0,
            current_value REAL DEFAULT 0.0,
            total_pnl REAL DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            company_name TEXT,
            quantity INTEGER NOT NULL DEFAULT 0,
            avg_buy_price REAL NOT NULL DEFAULT 0.0,
            product_type TEXT DEFAULT 'CNC',
            UNIQUE(user_id, symbol, product_type),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            company_name TEXT,
            order_type TEXT NOT NULL,
            product_type TEXT NOT NULL,
            price_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'EXECUTED',
            brokerage REAL DEFAULT 0.0,
            total_charges REAL DEFAULT 0.0,
            total_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS fund_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            balance_after REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            company_name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, symbol),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        conn.commit()
        conn.close()
        print("Database initialized successfully.")
        return

    ensure_database()
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            theme VARCHAR(20) DEFAULT 'dark',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS portfolio (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT UNIQUE NOT NULL,
            available_funds DOUBLE DEFAULT 1000000.0,
            total_invested DOUBLE DEFAULT 0.0,
            current_value DOUBLE DEFAULT 0.0,
            total_pnl DOUBLE DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS holdings (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            company_name VARCHAR(255),
            quantity INT NOT NULL DEFAULT 0,
            avg_buy_price DOUBLE NOT NULL DEFAULT 0.0,
            product_type VARCHAR(20) DEFAULT 'CNC',
            UNIQUE KEY unique_holding (user_id, symbol, product_type),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            company_name VARCHAR(255),
            order_type VARCHAR(20) NOT NULL,
            product_type VARCHAR(20) NOT NULL,
            price_type VARCHAR(20) NOT NULL,
            quantity INT NOT NULL,
            price DOUBLE NOT NULL,
            status VARCHAR(50) DEFAULT 'EXECUTED',
            brokerage DOUBLE DEFAULT 0.0,
            total_charges DOUBLE DEFAULT 0.0,
            total_amount DOUBLE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS fund_transactions (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            type VARCHAR(50) NOT NULL,
            amount DOUBLE NOT NULL,
            description VARCHAR(255),
            balance_after DOUBLE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS watchlist (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            company_name VARCHAR(255),
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_watchlist (user_id, symbol),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")
