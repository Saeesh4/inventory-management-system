import mysql.connector

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Admin@1234',
    database='inventory_db'
)
cur = con.cursor()
try:
    cur.execute("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
    con.commit()
    print('Status column added successfully!')
except Exception as e:
    print(f'Note: {e}')