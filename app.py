from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from flask import make_response

app = Flask(__name__)
app.secret_key = 'inventory_secret_key_2024'

def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Admin@1234',
        database='inventory_db'
    )

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user['password'], password):
            if user.get('status') == 'suspended':
                flash('Your account has been suspended. Contact admin.')
                return render_template('login.html')
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) as total FROM products")
    total_products = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM suppliers")
    total_suppliers = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM products WHERE quantity <= reorder_level")
    low_stock = cur.fetchone()['total']
    cur.execute("SELECT * FROM products WHERE quantity <= reorder_level")
    low_stock_items = cur.fetchall()
    return render_template('dashboard.html', 
        total_products=total_products,
        total_suppliers=total_suppliers,
        low_stock=low_stock,
        low_stock_items=low_stock_items)

@app.route('/products')
def products():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT p.*, s.name as supplier_name FROM products p LEFT JOIN suppliers s ON p.supplier_id = s.id")
    products = cur.fetchall()
    cur.execute("SELECT * FROM suppliers")
    suppliers = cur.fetchall()
    return render_template('products.html', products=products, suppliers=suppliers)

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'user' not in session:
        return redirect(url_for('login'))
    name = request.form['name']
    category = request.form['category']
    quantity = request.form['quantity']
    unit_price = request.form['unit_price']
    reorder_level = request.form['reorder_level']
    supplier_id = request.form['supplier_id']
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO products (name, category, quantity, unit_price, reorder_level, supplier_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, category, quantity, unit_price, reorder_level, supplier_id))
    db.commit()
    flash('Product added successfully!')
    return redirect(url_for('products'))

@app.route('/delete_product/<int:id>')
def delete_product(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (id,))
    db.commit()
    flash('Product deleted!')
    return redirect(url_for('products'))

@app.route('/suppliers')
def suppliers():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM suppliers")
    suppliers = cur.fetchall()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/add_supplier', methods=['POST'])
def add_supplier():
    if 'user' not in session:
        return redirect(url_for('login'))
    name = request.form['name']
    contact = request.form['contact']
    email = request.form['email']
    address = request.form['address']
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO suppliers (name, contact, email, address) VALUES (%s, %s, %s, %s)",
                (name, contact, email, address))
    db.commit()
    flash('Supplier added successfully!')
    return redirect(url_for('suppliers'))

@app.route('/delete_supplier/<int:id>')
def delete_supplier(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM suppliers WHERE id=%s", (id,))
    db.commit()
    flash('Supplier deleted!')
    return redirect(url_for('suppliers'))

@app.route('/transactions')
def transactions():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT t.*, p.name as product_name FROM transactions t LEFT JOIN products p ON t.product_id = p.id ORDER BY t.transaction_date DESC")
    transactions = cur.fetchall()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    return render_template('transactions.html', transactions=transactions, products=products)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'user' not in session:
        return redirect(url_for('login'))
    product_id = request.form['product_id']
    transaction_type = request.form['transaction_type']
    quantity = int(request.form['quantity'])
    notes = request.form['notes']
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO transactions (product_id, transaction_type, quantity, notes) VALUES (%s, %s, %s, %s)",
                (product_id, transaction_type, quantity, notes))
    if transaction_type == 'IN':
        cur.execute("UPDATE products SET quantity = quantity + %s WHERE id = %s", (quantity, product_id))
    else:
        cur.execute("UPDATE products SET quantity = quantity - %s WHERE id = %s", (quantity, product_id))
    db.commit()
    flash('Transaction recorded successfully!')
    return redirect(url_for('transactions'))

@app.route('/predict')
def predict():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    predictions = []
    accuracy_scores = []

    for product in products:
        # Get all OUT transactions
        cur.execute("""
            SELECT DATE(transaction_date) as date,
            SUM(quantity) as daily_qty
            FROM transactions
            WHERE product_id = %s AND transaction_type = 'OUT'
            GROUP BY DATE(transaction_date)
            ORDER BY date
        """, (product['id'],))
        daily_data = cur.fetchall()

        # Get total OUT and days
        cur.execute("""
            SELECT COALESCE(SUM(quantity), 0) as total_out
            FROM transactions
            WHERE product_id = %s AND transaction_type = 'OUT'
        """, (product['id'],))
        total_out = cur.fetchone()['total_out']

        days = len(daily_data)
        daily_avg = round(total_out / days, 2) if days > 0 else 0

        # Linear Regression prediction
        lr_daily_avg = daily_avg
        accuracy = 0

        if len(daily_data) >= 2:
            try:
                import numpy as np
                from sklearn.linear_model import LinearRegression

                X = np.array(range(len(daily_data))).reshape(-1, 1)
                y = np.array([float(d['daily_qty']) for d in daily_data])

                model = LinearRegression()
                model.fit(X, y)

                # Predict next day consumption
                next_day = np.array([[len(daily_data)]])
                lr_daily_avg = max(0, round(float(model.predict(next_day)[0]), 2))

                # Calculate accuracy: compare predicted vs actual
                y_pred = model.predict(X)
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                accuracy = max(0, round(r2 * 100, 1))
                accuracy_scores.append(accuracy)
            except:
                lr_daily_avg = daily_avg
                accuracy = 0

        # Days remaining
        days_remaining = round(product['quantity'] / lr_daily_avg, 1) if lr_daily_avg > 0 else 999

        # Reorder schedule
        if days_remaining <= 3:
            reorder_urgency = 'URGENT - Reorder Today!'
            urgency_color = 'danger'
        elif days_remaining <= 7:
            reorder_urgency = f'Reorder within {int(days_remaining)} days'
            urgency_color = 'warning'
        elif days_remaining <= 14:
            reorder_urgency = f'Reorder within {int(days_remaining)} days'
            urgency_color = 'info'
        else:
            reorder_urgency = f'Stock sufficient for {int(days_remaining)} days'
            urgency_color = 'success'

        # Reorder needed flag
        reorder_needed = product['quantity'] <= product['reorder_level']

        # Overstock detection (more than 5x reorder level)
        overstock = product['quantity'] > (product['reorder_level'] * 5)

        # Suggested order quantity
        suggested_order = max(0, (product['reorder_level'] * 3) - product['quantity'])

        predictions.append({
            'name': product['name'],
            'category': product['category'],
            'current_stock': product['quantity'],
            'reorder_level': product['reorder_level'],
            'daily_avg': daily_avg,
            'lr_daily_avg': lr_daily_avg,
            'days_remaining': days_remaining,
            'reorder_needed': reorder_needed,
            'overstock': overstock,
            'suggested_order': suggested_order,
            'reorder_urgency': reorder_urgency,
            'urgency_color': urgency_color,
            'accuracy': accuracy,
            'data_points': days
        })

    avg_accuracy = round(sum(accuracy_scores) / len(accuracy_scores), 1) if accuracy_scores else 0
    return render_template('predict.html', predictions=predictions, avg_accuracy=avg_accuracy)

@app.route('/reports')
def reports():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT p.name, SUM(t.quantity) as total_out FROM transactions t JOIN products p ON t.product_id = p.id WHERE t.transaction_type='OUT' GROUP BY p.name")
    stock_out_data = cur.fetchall()
    cur.execute("SELECT p.name, SUM(t.quantity) as total_in FROM transactions t JOIN products p ON t.product_id = p.id WHERE t.transaction_type='IN' GROUP BY p.name")
    stock_in_data = cur.fetchall()
    cur.execute("SELECT * FROM products WHERE quantity <= reorder_level")
    low_stock = cur.fetchall()
    cur.execute("SELECT COUNT(*) as total FROM transactions")
    total_transactions = cur.fetchone()['total']
    return render_template('reports.html',
        stock_out_data=stock_out_data,
        stock_in_data=stock_in_data,
        low_stock=low_stock,
        total_transactions=total_transactions)

@app.route('/export_csv')
def export_csv():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT t.id, p.name as product, t.transaction_type, t.quantity, t.transaction_date, t.notes FROM transactions t JOIN products p ON t.product_id = p.id ORDER BY t.transaction_date DESC")
    transactions = cur.fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Product', 'Type', 'Quantity', 'Date', 'Notes'])
    for t in transactions:
        writer.writerow([t['id'], t['product'], t['transaction_type'], t['quantity'], t['transaction_date'], t['notes']])
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=inventory_ledger.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route('/export_pdf')
def export_pdf():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT t.id, p.name as product, t.transaction_type, t.quantity, t.transaction_date, t.notes FROM transactions t JOIN products p ON t.product_id = p.id ORDER BY t.transaction_date DESC")
    transactions = cur.fetchall()
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 50, "Inventory Ledger Report")
    c.setFont("Helvetica-Bold", 10)
    y = height - 90
    c.drawString(30, y, "ID")
    c.drawString(60, y, "Product")
    c.drawString(180, y, "Type")
    c.drawString(260, y, "Quantity")
    c.drawString(330, y, "Date")
    c.drawString(480, y, "Notes")
    c.line(30, y - 5, width - 30, y - 5)
    c.setFont("Helvetica", 9)
    y -= 20
    for t in transactions:
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(30, y, str(t['id']))
        c.drawString(60, y, str(t['product'])[:15])
        c.drawString(180, y, str(t['transaction_type']))
        c.drawString(260, y, str(t['quantity']))
        c.drawString(330, y, str(t['transaction_date'])[:20])
        c.drawString(480, y, str(t['notes'] or '')[:10])
        y -= 20
    c.save()
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=inventory_ledger.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s", (session['user'],))
        user = cur.fetchone()
        if not check_password_hash(user['password'], current_password):
            flash('Current password is incorrect!', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match!', 'danger')
        elif len(new_password) < 6:
            flash('Password must be at least 6 characters!', 'danger')
        else:
            hashed = generate_password_hash(new_password)
            cur.execute("UPDATE users SET password=%s WHERE username=%s",
                       (hashed, session['user']))
            db.commit()
            flash('Password changed successfully!', 'success')
    return render_template('change_password.html')

@app.route('/import_excel', methods=['GET', 'POST'])
def import_excel():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        flash('Only admin can import data!')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!')
            return redirect(url_for('import_excel'))
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!')
            return redirect(url_for('import_excel'))
        if file and file.filename.endswith('.xlsx'):
            import pandas as pd
            import io
            products_added = 0
            transactions_added = 0
            db = get_db()
            cur = db.cursor()
            file_bytes = io.BytesIO(file.read())
            try:
                df_products = pd.read_excel(file_bytes, sheet_name='Products')
                for _, row in df_products.iterrows():
                    cur.execute("SELECT id FROM products WHERE name=%s", (str(row['name']),))
                    if not cur.fetchone():
                        cur.execute("""INSERT INTO products
                            (name, category, quantity, unit_price, reorder_level)
                            VALUES (%s, %s, %s, %s, %s)""",
                            (str(row['name']), str(row['category']),
                             int(row['quantity']), float(row['unit_price']),
                             int(row['reorder_level'])))
                        products_added += 1
            except Exception as e:
                flash(f'Products sheet error: {str(e)}')
            file_bytes.seek(0)
            try:
                df_trans = pd.read_excel(file_bytes, sheet_name='Transactions')
                for _, row in df_trans.iterrows():
                    cur.execute("SELECT id FROM products WHERE name=%s",
                               (str(row['product_name']),))
                    product = cur.fetchone()
                    if product:
                        t_type = str(row['transaction_type']).upper()
                        qty = int(row['quantity'])
                        try:
                            import pandas as pd2
                            t_date = pd.to_datetime(row['transaction_date']).strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            from datetime import datetime
                            t_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        notes = str(row['notes']) if pd.notna(row['notes']) else ''
                        cur.execute("""INSERT INTO transactions
                            (product_id, transaction_type, quantity,
                            transaction_date, notes)
                            VALUES (%s, %s, %s, %s, %s)""",
                            (product[0], t_type, qty, t_date, notes))
                        if t_type == 'IN':
                            cur.execute("UPDATE products SET quantity = quantity + %s WHERE id = %s",
                                       (qty, product[0]))
                        else:
                            cur.execute("UPDATE products SET quantity = GREATEST(0, quantity - %s) WHERE id = %s",
                                       (qty, product[0]))
                        transactions_added += 1
            except Exception as e:
                flash(f'Transactions sheet error: {str(e)}')
            db.commit()
            flash(f'Import successful! Products added: {products_added} | Transactions added: {transactions_added}')
            return redirect(url_for('import_excel'))
        else:
            flash('Please upload a .xlsx file only!')
    return render_template('import_excel.html')

@app.route('/manage_staff')
def manage_staff():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        flash('Only admin can manage staff!')
        return redirect(url_for('dashboard'))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE role != 'admin'")
    staff_list = cur.fetchall()
    return render_template('manage_staff.html', staff_list=staff_list)

@app.route('/add_staff', methods=['POST'])
def add_staff():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cur.fetchone():
        flash('Username already exists!')
        return redirect(url_for('manage_staff'))
    hashed = generate_password_hash(password)
    cur.execute("INSERT INTO users (username, password, role, status) VALUES (%s, %s, %s, 'active')",
                (username, hashed, role))
    db.commit()
    flash(f'Staff member {username} added successfully!')
    return redirect(url_for('manage_staff'))

@app.route('/delete_staff/<int:id>')
def delete_staff(id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT username FROM users WHERE id=%s AND role != 'admin'", (id,))
    user = cur.fetchone()
    if user:
        cur.execute("DELETE FROM users WHERE id=%s AND role != 'admin'", (id,))
        db.commit()
        flash(f"🗑️ {user['username']} has been removed successfully!")
    return redirect(url_for('manage_staff'))

@app.route('/suspend_staff/<int:id>')
def suspend_staff(id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE id=%s", (id,))
    user = cur.fetchone()
    if user:
        new_status = 'suspended' if user['status'] == 'active' else 'active'
        cur.execute("UPDATE users SET status=%s WHERE id=%s", (new_status, id))
        db.commit()
        if new_status == 'suspended':
            flash(f"⏸️ {user['username']} has been suspended successfully!")
        else:
            flash(f"✅ {user['username']} has been reactivated successfully!")
    return redirect(url_for('manage_staff'))

if __name__ == '__main__':
    app.run(debug=True)