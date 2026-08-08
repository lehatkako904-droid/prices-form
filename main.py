from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import uuid  # بۆ دروستکردنی ناسنامەی تایبەت

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ========== داتاکان (خەزنی کاتی) ==========
# پێکهاتەی فرۆشگا: {id, shop_name, showroom, company, phone, email, category, products: []}
shops_db = []
# پێکهاتەی کاڵا: {id, name, price, shop_id}
products_db = []

# زانیاری بەڕێوەبەر
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# پێناسەی کەتەگۆرییەکان بۆ نیشاندان
CATEGORY_LABELS = {
    "ئەلکترۆنیات": "ئەلکترۆنیات",
    "کارەباییات": "کارەباییات",
    "بیناسازی": "بیناسازی",
    "کەلوپەل": "کەلوپەل"
}

# ========== ڕاوتەکانی گشتی (بەبێ چوونەژوورەوە) ==========
@app.route('/')
def index():
    # هەموو کاڵاکان لەگەڵ ناوی فرۆشگا
    all_prices = []
    for p in products_db:
        shop = next((s for s in shops_db if s['id'] == p['shop_id']), None)
        all_prices.append({
            'store_name': shop['shop_name'] if shop else 'نەزانراو',
            'item_name': p['name'],
            'category': shop['category'] if shop else 'نەزانراو',
            'price': p['price']
        })
    return render_template('index.html', prices=all_prices)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        shop = {
            'id': str(uuid.uuid4()),
            'shop_name': request.form.get('name'),
            'showroom': request.form.get('showroom', ''),
            'company': request.form.get('company', ''),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'category': request.form.get('category'),
            'address': request.form.get('address', ''),
            'product_count': 0
        }
        shops_db.append(shop)
        flash('فرۆشگاکە بە سەرکەوتووی تۆمارکرا!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['role'] = 'admin'
            session['username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            error = "ناوی بەکارهێنەر یان وشەی تێپەڕ هەڵەیە!"
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    flash('دەرچوویت!', 'success')
    return redirect(url_for('index'))


# ========== ڕاوتەکانی بەڕێوەبەر (Admin) ==========
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['role'] = 'admin'
            session['username'] = username
            flash('بەخێربێیتەوە بەڕێوەبەر!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('ناوی بەکارهێنەر یان وشەی تێپەڕ هەڵەیە!', 'error')
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    # ئامارەکان
    stats = {
        'shops': len(shops_db),
        'products': len(products_db),
        'users': len(shops_db)  # لەم وەشەنەدا هەر فرۆشگایەک وەک بەکارهێنەر دادەنرێت
    }

    # ژماردن کاڵا بۆ هەر فرۆشگایەک
    for shop in shops_db:
        shop['product_count'] = sum(1 for p in products_db if p['shop_id'] == shop['id'])

    return render_template(
        'admin.html',
        shops=shops_db,
        stats=stats,
        category_labels=CATEGORY_LABELS
    )


@app.route('/admin/compare')
def admin_compare():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    # کۆکردنەوەی کاڵاکان بەپێی ناو
    items_dict = {}
    for p in products_db:
        shop = next((s for s in shops_db if s['id'] == p['shop_id']), None)
        if not shop:
            continue
        iname = p['name']
        if iname not in items_dict:
            items_dict[iname] = {
                'name': iname,
                'prices': [],
                'count': 0
            }
        items_dict[iname]['prices'].append({
            'shop': shop['shop_name'],
            'showroom': shop.get('showroom', ''),
            'price': p['price']
        })
        items_dict[iname]['count'] += 1

    # دیاریکردنی کەمترین و زۆرترین بۆ هەر کاڵایەک
    items_list = []
    for iname, data in items_dict.items():
        prices = data['prices']
        min_price = min(prices, key=lambda x: x['price'])
        max_price = max(prices, key=lambda x: x['price'])
        items_list.append({
            'name': iname,
            'count': data['count'],
            'min': min_price,
            'max': max_price,
            'diff': max_price['price'] - min_price['price'],
            'prices': sorted(prices, key=lambda x: x['price'])
        })

    return render_template('compare.html', items=items_list)


@app.route('/admin/shop/<sid>')
def admin_shop(sid):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    shop = next((s for s in shops_db if s['id'] == sid), None)
    if not shop:
        flash('فرۆشگاکە نەدۆزرایەوە!', 'error')
        return redirect(url_for('admin_dashboard'))

    products = [p for p in products_db if p['shop_id'] == sid]
    return render_template(
        'admin_shop.html',
        shop=shop,
        products=products,
        category_labels=CATEGORY_LABELS
    )


@app.route('/admin/shop/<sid>/add', methods=['POST'])
def admin_add_product(sid):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    shop = next((s for s in shops_db if s['id'] == sid), None)
    if not shop:
        flash('فرۆشگاکە نەدۆزرایەوە!', 'error')
        return redirect(url_for('admin_dashboard'))

    name = request.form.get('name')
    price = request.form.get('price')
    if not name or not price:
        flash('ناو و نرخ پێویستە!', 'error')
        return redirect(url_for('admin_shop', sid=sid))

    try:
        price = float(price)
    except ValueError:
        flash('نرخەکە دروست نییە!', 'error')
        return redirect(url_for('admin_shop', sid=sid))

    new_product = {
        'id': str(uuid.uuid4()),
        'name': name,
        'price': price,
        'shop_id': sid
    }
    products_db.append(new_product)
    flash('کاڵا بە سەرکەوتووی زیادکرا!', 'success')
    return redirect(url_for('admin_shop', sid=sid))


@app.route('/admin/product/<pid>/update', methods=['POST'])
def admin_update_product(pid):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    product = next((p for p in products_db if p['id'] == pid), None)
    if not product:
        flash('کاڵاکە نەدۆزرایەوە!', 'error')
        return redirect(url_for('admin_dashboard'))

    name = request.form.get('name')
    price = request.form.get('price')
    if not name or not price:
        flash('ناو و نرخ پێویستە!', 'error')
        return redirect(url_for('admin_shop', sid=product['shop_id']))

    try:
        price = float(price)
    except ValueError:
        flash('نرخەکە دروست نییە!', 'error')
        return redirect(url_for('admin_shop', sid=product['shop_id']))

    product['name'] = name
    product['price'] = price
    flash('کاڵا نوێکرایەوە!', 'success')
    return redirect(url_for('admin_shop', sid=product['shop_id']))


@app.route('/admin/product/<pid>/delete', methods=['POST'])
def admin_delete_product(pid):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    product = next((p for p in products_db if p['id'] == pid), None)
    if not product:
        flash('کاڵاکە نەدۆزرایەوە!', 'error')
        return redirect(url_for('admin_dashboard'))

    shop_id = product['shop_id']
    products_db.remove(product)
    flash('کاڵا سڕایەوە!', 'success')
    return redirect(url_for('admin_shop', sid=shop_id))


@app.route('/market')
def market():
    # نمایش هەموو کاڵاکان لە بازاڕدا
    rows = []
    for p in products_db:
        shop = next((s for s in shops_db if s['id'] == p['shop_id']), None)
        if shop:
            rows.append({
                'name': p['name'],
                'shop_name': shop['shop_name'],
                'showroom': shop.get('showroom', ''),
                'category': shop.get('category', ''),
                'price': p['price']
            })
    return render_template('market.html', rows=rows, category_labels=CATEGORY_LABELS)


if __name__ == '__main__':
    app.run(debug=True)
