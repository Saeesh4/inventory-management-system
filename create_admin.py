import os
import mysql.connector
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

con = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'inventory_db')
)
cur = con.cursor()

admin_password = 'Admin@1234'
hashed = generate_password_hash(admin_password)

cur.execute("INSERT INTO users (username, password, role, status) VALUES ('admin', %s, 'admin', 'active')", (hashed,))
con.commit()
print('Admin user created successfully!')
print(f'Username: admin | Password: {admin_password}')
