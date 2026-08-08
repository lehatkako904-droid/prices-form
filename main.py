from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# داتای کاتی بۆ نموونە
users_db = []   # تۆمارکراوەکانی فرۆشگا
prices_db = []  # نرخەکان

# زانیاری بەڕێوەبەر
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

    # ----- شیکاری پێشکەوتوو بەپێی کەتەگۆری و کاڵا -----
    analysis = {}  # structure: {category: {item_name: {"min": item, "max": item, "all": []}}}
    for item in prices_db:
        cat = item['category']
        iname = item['item_name']
        # دڵنیابین لە بوونی پێکهاتەکان
        if cat not in analysis:
            analysis[cat] = {}
        if iname not in analysis[cat]:
            analysis[cat][iname] = {"min": item, "max": item, "all": []}
        # زیادکردن بۆ لیستی هەموو نرخەکان
        analysis[cat][iname]["all"].append(item)
        # نوێکردنەوەی کەمترین و زۆرترین
        if item['price'] < analysis[cat][iname]["min"]['price']:
            analysis[cat][iname]["min"] = item
        if item['price'] > analysis[cat][iname]["max"]['price']:
            analysis[cat][iname]["max"] = item

    # ----- ئامارەکانی کارتەکان -----
    total_stores = len(users_db)
    total_items = sum(len(items) for items in analysis.values())

    overall_min = None
    overall_max = None
    for cat, items in analysis.items():
        for iname, data in items.items():
            if overall_min is None or data['min']['price'] < overall_min['price']:
                overall_min = {
                    'item': iname,
                    'price': data['min']['price'],
                    'store': data['min']['store_name'],
                    'category': cat
                }
            if overall_max is None or data['max']['price'] > overall_max['price']:
                overall_max = {
                    'item': iname,
                    'price': data['max']['price'],
                    'store': data['max']['store_name'],
                    'category': cat
                }

    return render_template(
        'dashboard.html',
        prices=prices_db,
        analysis=analysis,            # پێکهاتەی پێشکەوتوو
        users=users_db,
        total_stores=total_stores,
        total_items=total_items,
        overall_min=overall_min,
        overall_max=overall_max
    )


@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
