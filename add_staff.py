import mysql.connector
from werkzeug.security import generate_password_hash

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Admin@1234',
    database='inventory_db'
)
cur = con.cursor()
hashed = generate_password_hash('staff123')
cur.execute("INSERT INTO users (username, password, role) VALUES ('staff', %s, 'staff')", (hashed,))
con.commit()
print('Staff user created! Username: staff | Password: staff123')