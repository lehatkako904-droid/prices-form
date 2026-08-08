from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_NAME = 'market.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# دروستکردنی خشتەکان ئەگەر نەبوون
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            shop_name TEXT NOT NULL,
            showroom TEXT,
            company TEXT,
            phone TEXT,
            email TEXT,
            category TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (shop_id) REFERENCES shops (id)
        )
    ''')
    
    # دروستکردنی ئەکاونتی سەرەکی بەڕێوەبەر ئەگەر هە نەبێت
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_pw = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', hashed_pw, 'admin'))
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    # گەڕان بەدوای هەموو نرخ و کاڵاکاندا بۆ پەڕەی سەرەکی
    prices = conn.execute('''
        SELECT p.*, s.shop_name, s.category 
        FROM products p 
        JOIN shops s ON p.shop_id = s.id
    ''').fetchall()
    conn.close()
    return render_template('index.html', prices=prices)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        shop_name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        category = request.form.get('category')
        showroom = request.form.get('showroom', '')
        company = request.form.get('company', '')

        if not username or not password or not shop_name:
            flash("تکایە خانە پێویستەکان پڕبکەرەوە!", "error")
            return redirect(url_for('register'))

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            hashed_pw = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'user')", (username, hashed_pw))
            user_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO shops (user_id, shop_name, showroom, company, phone, email, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, shop_name, showroom, company, phone, email, category))
            
            conn.commit()
            flash("تۆمارکردن سەرکەوتوو بوو، ئێستا دەتوانیت بچیتە ژوورەوە.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("ناوی بەکارهێنەر پێشتر تۆمارکراوە!", "error")
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            if user['role'] == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            error = "ناوی بەکارهێنەر یان وشەی تێپەڕ هەڵەیە!"
            
    return render_template('login.html', error=error)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    
    if request.method == 'POST':
        store_name = request.form.get('store_name')
        item_name = request.form.get('item_name')
        category = request.form.get('category')
        try:
            price = float(request.form.get('price'))
        except ValueError:
            price = 0.0

        # دۆزینەوەی فرۆشگا یان دروستکردنی ئەگەر نەبوو بە ناوی بەستراو
        shop = conn.execute("SELECT id FROM shops WHERE shop_name = ?", (store_name,)).fetchone()
        if shop:
            shop_id = shop['id']
        else:
            # دروستکردنی یەدەگ بۆ ئەکاونتی فرۆشگا
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'user')", (store_name.replace(" ", ""), generate_password_hash('123456')))
            u_id = cursor.lastrowid
            cursor.execute("INSERT INTO shops (user_id, shop_name, category) VALUES (?, ?, ?)", (u_id, store_name, category))
            shop_id = cursor.lastrowid
            conn.commit()

        conn.execute("INSERT INTO products (shop_id, name, price) VALUES (?, ?, ?)", (shop_id, item_name, price))
        conn.commit()
        return redirect(url_for('dashboard'))

    # هێنانی داتاکان بۆ داشبۆرد
    users = conn.execute("SELECT * FROM shops").fetchall()
    
    products_raw = conn.execute('''
        SELECT p.*, s.shop_name, s.category 
        FROM products p 
        JOIN shops s ON p.shop_id = s.id
    ''').fetchall()

    analysis = {}
    for item in products_raw:
        cat = item['category'] or 'گشتی'
        iname = item['name']
        if cat not in analysis:
            analysis[cat] = {}
        if iname not in analysis[cat]:
            analysis[cat][iname] = {"min": item, "max": item, "all": []}
        analysis[cat][iname]["all"].append(item)
        if item['price'] < analysis[cat][iname]["min"]['price']:
            analysis[cat][iname]["min"] = item
        if item['price'] > analysis[cat][iname]["max"]['price']:
            analysis[cat][iname]["max"] = item

    total_stores = len(users)
    total_items = sum(len(items) for items in analysis.values())

    overall_min = None
    overall_max = None
    for cat, items in analysis.items():
        for iname, data in items.items():
            if overall_min is None or data['min']['price'] < overall_min['price']:
                overall_min = {
                    'item': iname,
                    'price': data['min']['price'],
                    'store': data['min']['shop_name'],
                    'category': cat
                }
            if overall_max is None or data['max']['price'] > overall_max['price']:
                overall_max = {
                    'item': iname,
                    'price': data['max']['price'],
                    'store': data['max']['shop_name'],
                    'category': cat
                }

    conn.close()
    return render_template(
        'dashboard.html',
        analysis=analysis,
        users=users,
        total_stores=total_stores,
        total_items=total_items,
        overall_min=overall_min,
        overall_max=overall_max
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
