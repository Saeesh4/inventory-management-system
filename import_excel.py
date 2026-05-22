import pandas as pd
import mysql.connector
from datetime import datetime

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Admin@1234',
    database='inventory_db'
)
cur = con.cursor()

print("\n" + "="*50)
print("EXCEL DATA IMPORTER")
print("="*50)

# ── IMPORT PRODUCTS ──────────────────────────────
try:
    df_products = pd.read_excel('stock_data.xlsx', sheet_name='Products')
    print(f"\n📦 Found {len(df_products)} products to import...")
    
    products_added = 0
    for _, row in df_products.iterrows():
        # Check if product already exists
        cur.execute("SELECT id FROM products WHERE name=%s", (row['name'],))
        existing = cur.fetchone()
        
        if not existing:
            cur.execute("""
                INSERT INTO products 
                (name, category, quantity, unit_price, reorder_level)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                str(row['name']),
                str(row['category']),
                int(row['quantity']),
                float(row['unit_price']),
                int(row['reorder_level'])
            ))
            products_added += 1
            print(f"  ✅ Added product: {row['name']}")
        else:
            print(f"  ⚠️  Skipped (already exists): {row['name']}")
    
    con.commit()
    print(f"\n✅ Products imported: {products_added}")

except Exception as e:
    print(f"❌ Error importing products: {e}")

# ── IMPORT TRANSACTIONS ──────────────────────────
try:
    df_transactions = pd.read_excel('stock_data.xlsx', sheet_name='Transactions')
    print(f"\n🔄 Found {len(df_transactions)} transactions to import...")

    transactions_added = 0
    errors = 0

    for _, row in df_transactions.iterrows():
        # Find product ID by name
        cur.execute("SELECT id FROM products WHERE name=%s", (str(row['product_name']),))
        product = cur.fetchone()

        if not product:
            print(f"  ⚠️  Product not found: {row['product_name']} — skipping")
            errors += 1
            continue

        product_id = product[0]
        t_type = str(row['transaction_type']).upper()
        qty = int(row['quantity'])

        # Parse date
        try:
            t_date = pd.to_datetime(row['transaction_date']).strftime('%Y-%m-%d %H:%M:%S')
        except:
            t_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        notes = str(row['notes']) if pd.notna(row['notes']) else ''

        # Insert transaction
        cur.execute("""
            INSERT INTO transactions 
            (product_id, transaction_type, quantity, transaction_date, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (product_id, t_type, qty, t_date, notes))

        # Update product quantity
        if t_type == 'IN':
            cur.execute("UPDATE products SET quantity = quantity + %s WHERE id = %s",
                       (qty, product_id))
        else:
            cur.execute("UPDATE products SET quantity = GREATEST(0, quantity - %s) WHERE id = %s",
                       (qty, product_id))

        transactions_added += 1
        print(f"  ✅ {t_type} | {row['product_name']} | Qty: {qty}")

    con.commit()
    print(f"\n✅ Transactions imported: {transactions_added}")
    if errors > 0:
        print(f"⚠️  Skipped (product not found): {errors}")

except Exception as e:
    print(f"❌ Error importing transactions: {e}")

print("\n" + "="*50)
print("Import complete! Check your app to see the data.")
print("="*50 + "\n")