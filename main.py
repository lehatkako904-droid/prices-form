from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# داتای کاتی بۆ نموونە (دەتوانیت αργتر بەستەری پێشکەوتووی بەکاربهێنیت)
users_db = []  # بۆ خەزنکردنی تۆمارکراوەکانی فرۆشگا/کۆمپانیاکان
prices_db = [] # بۆ خەزنکردنی نرخەکان و کاتەگۆرییەکان

# زانیاری بەڕێوەبەر (Admin)
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

@app.route('/')
def index():
    return render_template('index.html', prices=prices_db)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        store_data = {
            "name": request.form.get('name'),
            "phone": request.form.get('phone'),
            "email": request.form.get('email'),
            "category": request.form.get('category'),
            "address": request.form.get('address')
        }
        users_db.append(store_data)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            error = "ناوی بەکارهێنەر یان وشەی تێپەڕ هەڵەیە!"
    return render_template('login.html', error=error)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        price_data = {
            "store_name": request.form.get('store_name'),
            "item_name": request.form.get('item_name'),
            "category": request.form.get('category'),
            "price": float(request.form.get('price'))
        }
        prices_db.append(price_data)
        return redirect(url_for('dashboard'))

    # شیکاری بۆ کەمترین و زۆرترین نرخ بۆ هەر کالا‌یەک
    analysis = {}
    for item in prices_db:
        iname = item['item_name']
        if iname not in analysis:
            analysis[iname] = {"min": item, "max": item, "all": []}
        
        analysis[iname]["all"].append(item)
        if item['price'] < analysis[iname]["min"]['price']:
            analysis[iname]["min"] = item
        if item['price'] > analysis[iname]["max"]['price']:
            analysis[iname]["max"] = item

    return render_template('dashboard.html', prices=prices_db, analysis=analysis, users=users_db)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
