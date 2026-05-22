import mysql.connector
from datetime import datetime, timedelta
import random

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Admin@1234',
    database='inventory_db'
)
cur = con.cursor()

# Get all product IDs
cur.execute("SELECT id, name, quantity FROM products")
products = cur.fetchall()

if not products:
    print("No products found! Add products first.")
    exit()

transaction_notes = [
    'Daily sale', 'Bulk sale', 'Customer order',
    'Stock received from supplier', 'Restocked',
    'Emergency restock', 'Regular consumption',
    'Weekly sale', 'Monthly restock'
]

# Generate 50 transactions over past 30 days
base_date = datetime.now() - timedelta(days=30)
count = 0

for i in range(50):
    product = random.choice(products)
    product_id = product[0]
    
    # Alternate between IN and OUT, more OUT than IN
    if i % 4 == 0:
        t_type = 'IN'
        qty = random.randint(20, 50)
    else:
        t_type = 'OUT'
        qty = random.randint(1, 10)
    
    t_date = base_date + timedelta(days=random.randint(0, 30))
    note = random.choice(transaction_notes)
    
    cur.execute("""
        INSERT INTO transactions 
        (product_id, transaction_type, quantity, transaction_date, notes)
        VALUES (%s, %s, %s, %s, %s)
    """, (product_id, t_type, qty, t_date, note))
    
    # Update product quantity
    if t_type == 'IN':
        cur.execute("UPDATE products SET quantity = quantity + %s WHERE id = %s", (qty, product_id))
    else:
        cur.execute("UPDATE products SET quantity = GREATEST(0, quantity - %s) WHERE id = %s", (qty, product_id))
    
    count += 1

con.commit()
print(f'Successfully generated {count} historical transactions over the past 30 days!')