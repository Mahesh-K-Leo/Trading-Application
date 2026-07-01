from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify
from database import get_db, execute_query
import bcrypt
import re

auth_bp = Blueprint('auth', __name__)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, password FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            cursor.close()
            
            if user and verify_password(password, user[2]):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['theme'] = 'light'
                if request.is_json:
                    return jsonify({'success': True, 'redirect': '/dashboard'})
                return redirect('/dashboard')
            else:
                msg = 'Invalid email or password'
                if request.is_json:
                    return jsonify({'success': False, 'message': msg}), 401
                return render_template('login.html', error=msg)
        except Exception as e:
            error_msg = f'Login error: {str(e)}'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 500
            return render_template('login.html', error=error_msg)
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not email or not password:
            msg = 'All fields required'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            return render_template('register.html', error=msg)
        
        if len(password) < 6:
            msg = 'Password must be at least 6 characters'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            return render_template('register.html', error=msg)
        
        if not validate_email(email):
            msg = 'Invalid email format'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            return render_template('register.html', error=msg)
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = %s OR username = %s', (email, username))
            if cursor.fetchone():
                msg = 'Email or username already exists'
                if request.is_json:
                    return jsonify({'success': False, 'message': msg}), 409
                return render_template('register.html', error=msg)
            
            hashed_pw = hash_password(password)
            cursor.execute(
                'INSERT INTO users (username, email, password, balance) VALUES (%s, %s, %s, 1000000)',
                (username, email, hashed_pw)
            )
            conn.commit()
            user_id = cursor.lastrowid
            cursor.close()
            
            session['user_id'] = user_id
            session['username'] = username
            session['theme'] = 'light'
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': '/dashboard'})
            return redirect('/dashboard')
        except Exception as e:
            error_msg = f'Registration error: {str(e)}'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 500
            return render_template('register.html', error=error_msg)
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
