import mysql.connector
from werkzeug.security import generate_password_hash

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Admin@1234',
    database='inventory_db'
)
cur = con.cursor()

# Fix all users to have active status
cur.execute("UPDATE users SET status='active' WHERE status IS NULL OR status=''")

# Check all users
cur.execute("SELECT id, username, role, status FROM users")
users = cur.fetchall()
print("\nAll users in database:")
for u in users:
    print(f"  ID:{u[0]} | Username:{u[1]} | Role:{u[2]} | Status:{u[3]}")

con.commit()
print("\nAll users status fixed to active!")