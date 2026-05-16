from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector
from functools import wraps

app = Flask(__name__)
app.secret_key = 'xalco_secret_key_123'

# Connection-ka Database-ka
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="xalco_db"
    )

# Amniga Admin-ka
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user']['role'] != 'admin':
            return jsonify({"status": "error", "message": "Ma lihid ogolaansho!"}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', user=session['user'])

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (data['username'], data['password']))
    user = cursor.fetchone()
    conn.close()
    if user:
        session['user'] = user
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Username ama Password waa khalad!"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# --- API-YADA USERS ---
@app.route('/api/users', methods=['GET', 'POST', 'DELETE'])
@admin_required
def api_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        data = request.json
        if data.get('id'):
            cursor.execute("UPDATE users SET fullname=%s, username=%s, password=%s, role=%s WHERE id=%s",
                           (data['fullname'], data['username'], data['password'], data['role'], data['id']))
        else:
            cursor.execute("INSERT INTO users (fullname, username, password, role) VALUES (%s, %s, %s, %s)",
                           (data['fullname'], data['username'], data['password'], data['role']))
        conn.commit()
    elif request.method == 'DELETE':
        cursor.execute("DELETE FROM users WHERE id=%s", (request.args.get('id'),))
        conn.commit()
    cursor.execute("SELECT id, fullname, username, role, status FROM users")
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)

# --- API-YADA PRODUCTS ---
@app.route('/get_products')
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    prods = cursor.fetchall()
    conn.close()
    return jsonify(prods)

@app.route('/api/products', methods=['POST', 'DELETE'])
@admin_required
def api_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        if data.get('id'):
            cursor.execute("UPDATE products SET name=%s, price=%s WHERE id=%s", (data['name'], data['price'], data['id']))
        else:
            cursor.execute("INSERT INTO products (name, price) VALUES (%s, %s)", (data['name'], data['price']))
        conn.commit()
    elif request.method == 'DELETE':
        cursor.execute("DELETE FROM products WHERE id=%s", (request.args.get('id'),))
        conn.commit()
    conn.close()
    return jsonify({"status": "success"})

# --- API-YADA TABLES ---
@app.route('/api/tables', methods=['GET', 'POST', 'DELETE'])
@admin_required
def api_tables():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        data = request.json
        cursor.execute("INSERT INTO tables (table_num, guest_count) VALUES (%s, 0) ON DUPLICATE KEY UPDATE table_num=table_num", (data['table_num'],))
        conn.commit()
    elif request.method == 'DELETE':
        cursor.execute("DELETE FROM tables WHERE table_num=%s", (request.args.get('num'),))
        conn.commit()
    cursor.execute("SELECT * FROM tables ORDER BY table_num")
    res = cursor.fetchall()
    conn.close()
    return jsonify(res)

# --- API-YADA PAYMENTS ---
@app.route('/api/payments', methods=['GET', 'POST', 'DELETE'])
@admin_required
def api_payments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        cursor.execute("INSERT INTO payment_methods (method_name) VALUES (%s)", (request.json['name'],))
        conn.commit()
    elif request.method == 'DELETE':
        cursor.execute("DELETE FROM payment_methods WHERE id=%s", (request.args.get('id'),))
        conn.commit()
    cursor.execute("SELECT * FROM payment_methods")
    res = cursor.fetchall()
    conn.close()
    return jsonify(res)

# --- PROFILE & ORDERS ---
@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET profile_img=%s WHERE id=%s", (data['image'], session['user']['id']))
    conn.commit()
    session['user']['profile_img'] = data['image']
    session.modified = True
    conn.close()
    return jsonify({"status": "success"})

@app.route('/complete_order', methods=['POST'])
def complete_order():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Kaydi order-ka si loo helo ID cusub (Invoice ID)
    cursor.execute("INSERT INTO orders (total_amount) VALUES (%s)", (data['total'],))
    order_id = cursor.lastrowid
    
    # 2. Kordhi guest count-ka miiska
    cursor.execute("UPDATE tables SET guest_count = guest_count + 1 WHERE table_num = %s", (data['table_num'],))
    
    conn.commit()
    conn.close()
    
    # Soo celi ID-ga oo loo qaabeeyay #0001
    formatted_id = f"#{order_id:04d}"
    return jsonify({"status": "success", "invoice_id": formatted_id})

if __name__ == '__main__':
    app.run(debug=True)