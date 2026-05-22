import mysql.connector

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Admin@1234',
    database='inventory_db'
)
cur = con.cursor()
cur.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
con.commit()
print('Admin user created successfully!')