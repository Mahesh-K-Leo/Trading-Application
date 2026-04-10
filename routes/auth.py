from flask import Blueprint, request, session, redirect, url_for, render_template, flash
import bcrypt
from database import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '').strip()
        if not identifier or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE username=? OR email=?', (identifier, identifier)
        ).fetchone()
        conn.close()
        if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['theme'] = user['theme']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not all([full_name, username, email, password]):
            flash('Please fill in all fields.', 'error')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = get_db()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password_hash, full_name) VALUES (?,?,?,?)',
                (username, email, hashed, full_name)
            )
            conn.commit()
            user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
            conn.execute(
                'INSERT INTO portfolio (user_id, available_funds) VALUES (?,?)',
                (user['id'], 1000000.0)
            )
            conn.execute(
                'INSERT INTO fund_transactions (user_id, type, amount, description, balance_after) VALUES (?,?,?,?,?)',
                (user['id'], 'CREDIT', 1000000.0, 'Welcome bonus - Starting funds', 1000000.0)
            )
            conn.commit()
            conn.close()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            conn.close()
            flash('Username or email already exists.', 'error')
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
