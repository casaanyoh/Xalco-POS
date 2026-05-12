from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector

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

# 1. Bogga ugu horreeya
@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', user=session['user'])

# 2. Bogga Login-ka
@app.route('/login_page')
def login_page():
    return render_template('login.html')

# 3. API-ga Login-ka
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

# 4. API-ga Alaabta (Products)
@app.route('/get_products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return jsonify(products)

# 5. Kordhinta Guest-ga (IMPORTANT: Kan ayaad u baahnayd)
@app.route('/complete_order', methods=['POST'])
def complete_order():
    if 'user' not in session:
        return jsonify({"status": "error", "message": "Fadlan login samee"}), 401
    
    data = request.json
    table_num = data.get('table_num')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Kordhi guest_count-ka miiska la doortay
    cursor.execute("UPDATE tables SET guest_count = guest_count + 1 WHERE table_num = %s", (table_num,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

# 6. Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)

    # --- CRUD: PRODUCTS ---
@app.route('/api/products', methods=['GET', 'POST', 'DELETE'])
def api_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        data = request.json
        if 'id' in data: # EDIT
            cursor.execute("UPDATE products SET name=%s, price=%s WHERE id=%s", (data['name'], data['price'], data['id']))
        else: # NEW (Validation included)
            cursor.execute("SELECT id FROM products WHERE name=%s", (data['name'],))
            if cursor.fetchone(): return jsonify({"status":"error", "message":"Alaabtan horay ayay u jirtay!"})
            cursor.execute("INSERT INTO products (name, price) VALUES (%s, %s)", (data['name'], data['price']))
        conn.commit()
    
    elif request.method == 'DELETE':
        id = request.args.get('id')
        cursor.execute("DELETE FROM products WHERE id=%s", (id,))
        conn.commit()

    cursor.execute("SELECT * FROM products")
    prods = cursor.fetchall()
    conn.close()
    return jsonify(prods)

# --- CRUD: PAYMENTS ---
@app.route('/api/payments', methods=['GET', 'POST', 'DELETE'])
def api_payments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        data = request.json
        cursor.execute("INSERT INTO payment_methods (method_name) VALUES (%s) ON DUPLICATE KEY UPDATE method_name=%s", (data['name'], data['name']))
        conn.commit()
    elif request.method == 'DELETE':
        cursor.execute("DELETE FROM payment_methods WHERE id=%s", (request.args.get('id'),))
        conn.commit()
    
    cursor.execute("SELECT * FROM payment_methods")
    pays = cursor.fetchall()
    conn.close()
    return jsonify(pays)