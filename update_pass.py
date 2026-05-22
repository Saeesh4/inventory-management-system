import mysql.connector

con = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Admin@1234',
    database='inventory_db'
)
cur = con.cursor()
hashed = 'scrypt:32768:8:1$VfdjewokHscppYYC$b7bd078510b56ee1b70d8af7fa89847d70fe7a908295084b9d0c051d2756ef3a442a6bd1d7e34ffb3aece7c1b6432baba982fa742f5225e10357c7b0c2a3bfb3'
cur.execute("UPDATE users SET password=%s WHERE username='admin'", (hashed,))
con.commit()
print('Password updated successfully!')